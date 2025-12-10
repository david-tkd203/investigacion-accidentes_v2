import json
import html
from graphviz import Digraph
from typing import Dict, List, Optional


class CausalTree:
    ROOT_KEY = "0.0.0.0.0.0.0.0.0"

    

    def __init__(self, arbol_json_5q: str):
        self.arbol_json_5q = arbol_json_5q
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict[str, str]] = []
        self.current: Optional[str] = None
        self._build_tree()

    def _get_parent_key(self, key_str: str) -> Optional[str]:
        parts = list(map(int, key_str.split('.')))
        for i in reversed(range(len(parts))):
            if parts[i] != 0:
                parent_parts = parts.copy()
                parent_parts[i] = 0
                return '.'.join(map(str, parent_parts))
        return None

    def _get_level(self, key: str) -> int:
        return sum(1 for part in key.split('.') if part != '0')
    def suggest_child_targets(self) -> List[Dict[str, str]]:
        """
        Devuelve las ramas (hijos directos del nodo actual) a las que
        podrías 'adjuntar' el nuevo hijo, en lugar de crear una rama nueva.

        Estructura: [{"id": <child_id>, "label": <texto>}, ...]
        Si no hay hijos actuales, devuelve [].
        """
        if not self.current:
            return []
        curr_children = self.nodes.get(self.current, {}).get('children', [])
        return [{"id": cid, "label": self.nodes[cid]['label']} for cid in curr_children]
    
    def insert_between_parent_and_child(self, parent_id: str, target_child_id: str, new_label: str) -> bool:
        """
        Inserta un nuevo nodo ENTRE 'parent_id' y su hijo directo 'target_child_id'.
        El nuevo nodo toma la clave del hijo (ocupa su lugar) y el hijo (con TODO
        su subárbol) pasa a colgar de este nuevo nodo, reenumerando las claves 5Q
        para mantener una sola rama (lineal) bajo el nodo interpuesto.
        """
        # --- validaciones básicas ---
        if parent_id not in self.nodes or target_child_id not in self.nodes:
            return False
        if self.nodes[target_child_id]['parent'] != parent_id:
            return False

        interposed_id = target_child_id  # el nuevo nodo usará esta misma clave

        # --- 1) tomar un snapshot del subárbol original (por children reales) ---
        subtree_ids = []
        stack = [target_child_id]
        seen = set()
        while stack:
            nid = stack.pop()
            if nid in seen:
                continue
            seen.add(nid)
            subtree_ids.append(nid)
            for cid in self.nodes[nid].get('children', []):
                stack.append(cid)

        old_snapshot = {
            nid: {
                'label': self.nodes[nid]['label'],
                'parent': self.nodes[nid]['parent'],
                'children': list(self.nodes[nid]['children'])
            }
            for nid in subtree_ids
        }

        # --- 2) eliminar físicamente el subárbol antiguo de self.nodes ---
        for oid in subtree_ids:
            self.nodes.pop(oid, None)

        # Asegurar que el padre mantiene como hijo la clave 'interposed_id'
        parent_children = self.nodes[parent_id]['children']
        if interposed_id not in parent_children:
            parent_children.append(interposed_id)

        # --- 3) crear el nodo interpuesto (usa la clave antigua del hijo) ---
        self.nodes[interposed_id] = {
            'label': new_label,
            'parent': parent_id,
            'children': []
        }

        # --- 4) crear el "nuevo" nodo raíz del subárbol movido, colgando del interpuesto ---
        moved_root_new_id = self._generate_child_key(interposed_id)  # típicamente ...1
        root_old = old_snapshot[interposed_id]
        self.nodes[moved_root_new_id] = {
            'label': root_old['label'],
            'parent': interposed_id,
            'children': []
        }
        self.nodes[interposed_id]['children'].append(moved_root_new_id)

        # Mapeo old->new de ids dentro del subárbol (el antiguo root ahora es moved_root_new_id)
        id_map = {interposed_id: moved_root_new_id}

        # --- 5) recorrer el subárbol antiguo y reconstruir bajo el nuevo root, reenumerando ---
        queue = list(root_old['children'])  # hijos directos del antiguo root
        while queue:
            old_id = queue.pop(0)
            old_parent = old_snapshot[old_id]['parent']
            new_parent = id_map.get(old_parent)
            if not new_parent:
                # no debería ocurrir; seguridad
                continue

            # asignar nueva clave 5Q secuencial para este hijo bajo su nuevo padre
            new_id = self._generate_child_key(new_parent)

            # crear el nodo en la nueva estructura
            self.nodes[new_id] = {
                'label': old_snapshot[old_id]['label'],
                'parent': new_parent,
                'children': []
            }
            # enlazar desde el nuevo padre
            self.nodes[new_parent]['children'].append(new_id)

            # registrar en el mapeo y encolar sus hijos
            id_map[old_id] = new_id
            for gc in old_snapshot[old_id]['children']:
                queue.append(gc)

        # --- 6) reconstruir edges a partir de la nueva relación padre-hijo ---
        self.edges = []
        for nid, nd in self.nodes.items():
            for cid in nd.get('children', []):
                if cid in self.nodes:
                    # forzar consistencia de parent
                    if self.nodes[cid]['parent'] != nid:
                        self.nodes[cid]['parent'] = nid
                    self.edges.append({'from': nid, 'to': cid})

        # seleccionar el nodo interpuesto como "actual"
        self.current = interposed_id
        return True
    def _build_tree(self):
        data = json.loads(self.arbol_json_5q)
        root_key = self.ROOT_KEY
        if root_key not in data:
            raise ValueError(f"Falta nodo raíz ({root_key}).")

        sorted_keys = sorted(data.keys(), key=self._get_level)
        for key in sorted_keys:
            pkey = self._get_parent_key(key)
            self.nodes[key] = {
                'label': data[key],
                'parent': pkey,
                'children': []
            }
            if pkey and pkey in self.nodes:
                self.nodes[pkey]['children'].append(key)
                self.edges.append({'from': pkey, 'to': key})

        self.current = root_key

    def _generate_child_key(self, parent_id: str) -> str:
        if parent_id not in self.nodes:
            raise ValueError(f"Padre inválido: {parent_id}")

        parts = list(map(int, parent_id.split('.')))
        # profundidad del padre = número de segmentos no-cero
        depth = self._get_level(parent_id)  # 0 para raíz, 1 para primer nivel, etc.

        if depth >= len(parts):
            raise ValueError("Profundidad máxima alcanzada")

        # El hijo debe ocupar el PRIMER cero a la derecha del nivel del padre
        # (que normalmente es justo en 'depth')
        slot = None
        if parts[depth] == 0:
            slot = depth
        else:
            # si por algún motivo no es cero, buscamos el primer cero a la derecha
            for i in range(depth, len(parts)):
                if parts[i] == 0:
                    slot = i
                    break
        if slot is None:
            raise ValueError("No hay slot disponible para hijo")

        # siguiente índice: 1 + índice máximo actual de los hijos en ese slot
        children = self.nodes[parent_id].get('children', [])
        if children:
            # el índice del hijo en 5Q es el dígito en 'slot' de cada hijo
            try:
                max_idx = max(int(ch.split('.')[slot]) for ch in children)
            except Exception:
                max_idx = len(children)
            next_idx = max_idx + 1
        else:
            next_idx = 1

        new_parts = parts.copy()
        new_parts[slot] = next_idx
        # todo lo que esté a la derecha del slot se deja en cero
        for j in range(slot + 1, len(new_parts)):
            new_parts[j] = 0

        return '.'.join(map(str, new_parts))

    def wrap_text(self, text: str, max_width: int = 25) -> List[str]:
        words, lines, curr = text.split(), [], []
        for w in words:
            if len(' '.join(curr + [w])) <= max_width:
                curr.append(w)
            else:
                lines.append(' '.join(curr))
                curr = [w]
        if curr:
            lines.append(' '.join(curr))
        return lines

    def generate_dot(self, base_path: Optional[str] = None) -> str:
        dot = Digraph()
        dot.attr(bgcolor='#ffffff', compound='true', dir='back', newrank='true',
                 nodesep='0.3', rankdir='TB', ranksep='0.4')
        dot.attr('node',
                 shape='Mrecord', style='filled,rounded',
                 fillcolor='#ffffff', gradientangle='270',
                 color="#B8B8B8", fontname='Arial', fontsize='10pt',
                 penwidth='1.5', width='2.0', height='1.0',
                 margin='0.1,0.1', dir='back')
        dot.attr('edge', color='#606060', penwidth='0.8')

        for nid, data in self.nodes.items():
            lines = self.wrap_text(data['label'])
            escaped = [f"<FONT>{html.escape(ln)}</FONT>" for ln in lines]
            label = f"<{ '<BR/>'.join(escaped) }>"
            attrs = {}
            if nid == self.current:
                attrs.update({
                    'fillcolor': "#ECEAEA",
                    'color': "#575757",
                    'penwidth': '3',
                    'fontname': 'Arial'
                })
            if base_path:
                attrs['URL'] = f"{base_path}?action=navigate_to&node_id={nid}"
                attrs['target'] = '_self'
            dot.node(nid, label=label, **attrs)

        for e in self.edges:
            dot.edge(e['from'], e['to'], arrowhead='inv', dir='back')

        return dot.source

    def get_breadcrumbs(self) -> str:
        curr = self.current
        path = []
        while curr:
            path.append(self.nodes[curr]['label'])
            curr = self.nodes[curr]['parent']
        return " > ".join(reversed(path))

    def get_current_label(self) -> str:
        return self.nodes[self.current]['label'] if self.current else ""

    def export_to_5q_json(self) -> str:
        return json.dumps({nid: data['label'] for nid, data in self.nodes.items()}, ensure_ascii=False)

    def set_current(self, node_id: str):
        if node_id in self.nodes:
            self.current = node_id

    def navigate_to_parent(self):
        if self.current:
            parent = self.nodes[self.current]['parent']
            if parent:
                self.current = parent

    def navigate_to_root(self):
        self.current = self.ROOT_KEY

    def navigate_to_first_child(self):
        if self.current and self.nodes[self.current]['children']:
            self.current = self.nodes[self.current]['children'][0]

    def navigate_previous_cousin(self):
        if self.current:
            parent = self.nodes[self.current]['parent']
            if parent:
                siblings = self.nodes[parent]['children']
                idx = siblings.index(self.current)
                if idx > 0:
                    self.current = siblings[idx - 1]
    
    def navigate_next_cousin(self) -> bool:
        """
        Mueve al siguiente hermano (cousin) si existe.
        Si estamos en el nodo raíz, desciende al primer hijo.
        """
        if not self.current:
            return False

        # Caso especial: si estamos en el nodo raíz
        if self.current == self.ROOT_KEY:
            hijos = self.nodes[self.current]['children']
            if hijos:
                self.current = hijos[0]
                return True
            return False

        parent_id = self.nodes[self.current]['parent']
        if not parent_id:
            return False

        hermanos = self.nodes[parent_id]['children']
        if self.current not in hermanos:
            return False

        idx = hermanos.index(self.current)
        if idx + 1 < len(hermanos):
            self.current = hermanos[idx + 1]
            return True

        return False  # No hay más hermanos a la derecha

    def update_current_label(self, new_label: str) -> bool:
        if self.current and new_label:
            self.nodes[self.current]['label'] = new_label
            return True
        return False

    def add_child_node(self, label: str, attach_to: Optional[str] = None):
        """
        Agrega un hijo.
        - Por defecto (attach_to=None): crea una **nueva rama** como hijo directo del nodo actual.
        - Si attach_to es el ID de un hijo *existente* del nodo actual, INTERCALA el nuevo nodo
        ENTRE el actual (padre) y esa rama seleccionada (no lo deja debajo).
        """
        if not self.current:
            return

        # Caso 2: intercalar entre el padre (self.current) y un hijo ya existente (attach_to)
        if attach_to and attach_to in self.nodes:
            parent_of_attach = self.nodes[attach_to]['parent']
            if parent_of_attach == self.current:
                # Inserta "entre medio"
                self.insert_between_parent_and_child(self.current, attach_to, label)
                return
            # Si attach_to no es hijo directo del actual, caemos al caso por defecto.

        # Caso 1 (por defecto): crear una **nueva rama** bajo el nodo actual
        new_id = self._generate_child_key(self.current)
        self.nodes[new_id] = {
            'label': label,
            'parent': self.current,
            'children': []
        }
        self.nodes[self.current]['children'].append(new_id)
        self.edges.append({'from': self.current, 'to': new_id})

    def add_sibling_node(self, label: str) -> bool:
        if not self.current:
            return False

        current_id = self.current
        parent_id = self.nodes[current_id]['parent']
        if not parent_id:
            # No se puede crear hermano del nodo raíz
            return False

        # La posición (slot) del hermano corresponde al nivel del padre
        # (es decir, el índice donde el hijo coloca su dígito)
        slot = self._get_level(parent_id)  # 0-based
        siblings = self.nodes[parent_id].get('children', [])

        if siblings:
            try:
                max_idx = max(int(s.split('.')[slot]) for s in siblings)
            except Exception:
                max_idx = len(siblings)
            next_idx = max_idx + 1
        else:
            next_idx = 1

        # La nueva clave del hermano se construye desde el padre colocando 'next_idx' en 'slot'
        parts = list(map(int, parent_id.split('.')))
        parts[slot] = next_idx
        for i in range(slot + 1, len(parts)):
            parts[i] = 0
        new_id = '.'.join(map(str, parts))

        self.nodes[new_id] = {
            'label': label,
            'parent': parent_id,
            'children': []
        }
        self.nodes[parent_id]['children'].append(new_id)
        self.edges.append({'from': parent_id, 'to': new_id})
        self.current = new_id
        return True

    # ====================== ELIMINACIÓN (corregida) ======================

    def _delete_subtree(self, node_id: str):
        """
        Elimina node_id y todos sus descendientes (nodos y aristas),
        y lo quita de la lista de hijos del padre si corresponde.
        """
        if node_id not in self.nodes:
            return

        # 1) Borrar recursivamente todos los descendientes
        for child in list(self.nodes[node_id]['children']):
            self._delete_subtree(child)

        # 2) Quitar referencia del padre (si existe)
        parent = self.nodes[node_id]['parent']
        if parent and node_id in self.nodes.get(parent, {}).get('children', []):
            self.nodes[parent]['children'].remove(node_id)

        # 3) Limpiar aristas relacionadas a este nodo
        self.edges = [e for e in self.edges if e['from'] != node_id and e['to'] != node_id]

        # 4) Eliminar el propio nodo
        self.nodes.pop(node_id, None)

    def delete_current_node(self) -> bool:
        """
        Elimina el nodo actual (y su subárbol) y mueve el puntero al padre.
        No elimina el nodo raíz.
        """
        if not self.current or self.current == self.ROOT_KEY:
            return False

        parent = self.nodes[self.current]['parent']
        self._delete_subtree(self.current)
        # Reposicionar puntero
        self.current = parent if parent in self.nodes else self.ROOT_KEY
        return True

    def delete_node(self, node_id: str) -> bool:
        """
        Elimina un node_id específico (y su subárbol).
        No permite eliminar la raíz.
        """
        if not node_id or node_id == self.ROOT_KEY or node_id not in self.nodes:
            return False

        was_current = (self.current == node_id)
        parent = self.nodes[node_id]['parent']

        self._delete_subtree(node_id)

        if was_current:
            self.current = parent if parent in self.nodes else self.ROOT_KEY

        return True
