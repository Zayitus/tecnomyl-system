# expert/inference_engine.py - Motor de inferencia avanzado
import ast
import operator
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class InferenceStep:
    """Representa un paso en el razonamiento del sistema experto"""
    rule_id: str
    rule_name: str
    condition: str
    condition_result: bool
    action: str
    timestamp: datetime = field(default_factory=datetime.now)
    facts_used: Dict[str, Any] = field(default_factory=dict)

@dataclass
class InferenceResult:
    """Resultado completo del motor de inferencia"""
    conclusions: List[str] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)
    steps: List[InferenceStep] = field(default_factory=list)
    final_facts: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0

class SafeExpressionEvaluator:
    """Evaluador seguro de expresiones lógicas"""
    
    # Operadores permitidos
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.And: lambda x, y: x and y,
        ast.Or: lambda x, y: x or y,
        ast.Not: operator.not_,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
    }
    
    # Funciones permitidas
    ALLOWED_FUNCTIONS = {
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'abs': abs,
        'min': min,
        'max': max,
    }
    
    def __init__(self, facts: Dict[str, Any]):
        self.facts = facts
        
    def evaluate(self, expression: str) -> Any:
        """Evalúa una expresión de forma segura"""
        try:
            # Parse de la expresión
            tree = ast.parse(expression, mode='eval')
            return self._eval_node(tree.body)
        except Exception as e:
            print(f"Error evaluando expresión '{expression}': {e}")
            return False
    
    def _eval_node(self, node) -> Any:
        """Evalúa un nodo AST de forma recursiva"""
        
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        elif isinstance(node, ast.Name):
            # Variables (hechos) y funciones especiales
            if node.id in self.ALLOWED_FUNCTIONS:
                return self.ALLOWED_FUNCTIONS[node.id]
            return self.facts.get(node.id, None)
        elif isinstance(node, ast.List):
            return [self._eval_node(item) for item in node.elts]
        elif isinstance(node, ast.Compare):
            # Comparaciones (>, <, ==, in, etc.)
            left = self._eval_node(node.left)
            result = True
            
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                if type(op) in self.ALLOWED_OPERATORS:
                    result = result and self.ALLOWED_OPERATORS[type(op)](left, right)
                    left = right  # Para comparaciones encadenadas
                else:
                    raise ValueError(f"Operador no permitido: {type(op)}")
            
            return result
        elif isinstance(node, ast.BoolOp):
            # Operadores lógicos (and, or)
            op_func = self.ALLOWED_OPERATORS.get(type(node.op))
            if not op_func:
                raise ValueError(f"Operador booleano no permitido: {type(node.op)}")
            
            values = [self._eval_node(value) for value in node.values]
            result = values[0]
            for value in values[1:]:
                result = op_func(result, value)
            return result
        elif isinstance(node, ast.UnaryOp):
            # Operadores unarios (not, -, +)
            op_func = self.ALLOWED_OPERATORS.get(type(node.op))
            if not op_func:
                raise ValueError(f"Operador unario no permitido: {type(node.op)}")
            return op_func(self._eval_node(node.operand))
        elif isinstance(node, ast.Call):
            # Llamadas a funciones permitidas
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                # Funciones estándar permitidas
                if func_name in self.ALLOWED_FUNCTIONS:
                    func = self.ALLOWED_FUNCTIONS[func_name]
                    args = [self._eval_node(arg) for arg in node.args]
                    return func(*args)
                # Funciones especiales en facts
                elif func_name in self.facts and callable(self.facts[func_name]):
                    func = self.facts[func_name]
                    args = [self._eval_node(arg) for arg in node.args]
                    return func(*args)
                else:
                    raise ValueError(f"Función no permitida: {func_name}")
            else:
                raise ValueError(f"Función no permitida: {node.func}")
        else:
            raise ValueError(f"Nodo AST no permitido: {type(node)}")

class InferenceEngine:
    """Motor de inferencia con encadenamiento hacia adelante"""
    
    def __init__(self, rules_file: str = 'expert/advanced_rules.json'):
        self.rules = self._load_rules(rules_file)
        self.facts = {}
        self.inference_steps = []
    
    def _load_rules(self, rules_file: str) -> List[Dict]:
        """Carga las reglas desde archivo JSON"""
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return sorted(data.get('rules', []), key=lambda x: x.get('priority', 999))
        except Exception as e:
            print(f"Error cargando reglas: {e}")
            return []
    
    def forward_chaining(self, initial_facts: Dict[str, Any], max_iterations: int = 100) -> InferenceResult:
        """Ejecuta encadenamiento hacia adelante"""
        start_time = datetime.now()
        
        # Inicializar hechos
        self.facts = initial_facts.copy()
        self.facts['now'] = datetime.now()  # Función especial para fechas
        self.inference_steps = []
        
        conclusions = []
        actions_taken = []
        
        # Agregar funciones especiales a los hechos
        self._add_special_functions()
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            rule_fired = False
            
            for rule in self.rules:
                if self._should_evaluate_rule(rule):
                    step = self._evaluate_rule(rule)
                    
                    if step and step.condition_result:
                        # Regla disparada
                        self.inference_steps.append(step)
                        
                        # Ejecutar acción
                        action_result = self._execute_action(rule['action'], rule)
                        if action_result:
                            actions_taken.append(action_result)
                            conclusions.append(step.rule_name)
                        
                        rule_fired = True
                        
                        # Marcar regla como ejecutada para evitar loops
                        self.facts[f"rule_{rule['id']}_executed"] = True
                        
                        break  # Ejecutar una regla por iteración (prioridad)
            
            if not rule_fired:
                break  # No más reglas aplicables
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return InferenceResult(
            conclusions=conclusions,
            actions_taken=actions_taken,
            steps=self.inference_steps,
            final_facts=self.facts.copy(),
            execution_time=execution_time
        )
    
    def _add_special_functions(self):
        """Agregar funciones especiales disponibles en las reglas"""
        self.facts['days_since'] = lambda date: (datetime.now() - date).days if date else 999
        self.facts['hours_since'] = lambda date: (datetime.now() - date).total_seconds() / 3600 if date else 999
        self.facts['is_weekend'] = lambda: datetime.now().weekday() >= 5
        self.facts['current_hour'] = datetime.now().hour
    
    def _should_evaluate_rule(self, rule: Dict) -> bool:
        """Determina si una regla debe ser evaluada"""
        # No evaluar reglas ya ejecutadas (evitar loops infinitos)
        if self.facts.get(f"rule_{rule['id']}_executed", False):
            return False
        
        # Evaluar condiciones de activación si existen
        activation_condition = rule.get('activation_condition')
        if activation_condition:
            evaluator = SafeExpressionEvaluator(self.facts)
            return evaluator.evaluate(activation_condition)
        
        return True
    
    def _evaluate_rule(self, rule: Dict) -> Optional[InferenceStep]:
        """Evalúa una regla específica"""
        try:
            evaluator = SafeExpressionEvaluator(self.facts)
            condition_result = evaluator.evaluate(rule['condition'])
            
            # Capturar hechos utilizados en la evaluación
            facts_used = {k: v for k, v in self.facts.items() 
                         if isinstance(v, (str, int, float, bool, type(None)))}
            
            return InferenceStep(
                rule_id=rule['id'],
                rule_name=rule['name'],
                condition=rule['condition'],
                condition_result=bool(condition_result),
                action=rule['action'],
                facts_used=facts_used
            )
            
        except Exception as e:
            print(f"Error evaluando regla {rule['id']}: {e}")
            return None
    
    def _execute_action(self, action: str, rule: Dict) -> Optional[str]:
        """Ejecuta una acción de forma segura"""
        try:
            # Parsear acción (formato: función(argumentos))
            if '(' in action and ')' in action:
                func_name = action.split('(')[0].strip()
                args_str = action.split('(', 1)[1].rsplit(')', 1)[0]
                
                # Ejecutar acción según el tipo
                if func_name == 'add_observacion':
                    message = self._extract_string_arg(args_str)
                    self._add_observacion(message, rule)
                    return f"Observación agregada: {message}"
                
                elif func_name == 'mark_sanction':
                    self._mark_sanction(rule)
                    return "Sanción aplicada"
                
                elif func_name == 'set_fact':
                    # Formato: set_fact('nombre_hecho', valor)
                    parts = args_str.split(',', 1)
                    if len(parts) == 2:
                        fact_name = self._extract_string_arg(parts[0].strip())
                        fact_value = self._extract_string_arg(parts[1].strip())
                        self.facts[fact_name] = fact_value
                        return f"Hecho establecido: {fact_name} = {fact_value}"
                
                elif func_name == 'require_approval':
                    self._require_approval(rule)
                    return "Requiere aprobación supervisor"
                
                else:
                    print(f"Acción no reconocida: {func_name}")
                    return None
            
        except Exception as e:
            print(f"Error ejecutando acción '{action}': {e}")
            return None
    
    def _extract_string_arg(self, arg_str: str) -> str:
        """Extrae un argumento string de forma segura"""
        arg_str = arg_str.strip()
        if arg_str.startswith('"') and arg_str.endswith('"'):
            return arg_str[1:-1]
        elif arg_str.startswith("'") and arg_str.endswith("'"):
            return arg_str[1:-1]
        return arg_str
    
    def _add_observacion(self, message: str, rule: Dict):
        """Agrega una observación a los hechos"""
        if 'observaciones' not in self.facts:
            self.facts['observaciones'] = []
        
        severity = rule.get('severity', 'info')
        self.facts['observaciones'].append({
            'message': message,
            'severity': severity,
            'rule_id': rule['id'],
            'timestamp': datetime.now().isoformat()
        })
    
    def _mark_sanction(self, rule: Dict):
        """Marca que se debe aplicar una sanción"""
        self.facts['sancion_aplicada'] = True
        self.facts['sancion_motivo'] = rule.get('name', 'Regla del sistema experto')
    
    def _require_approval(self, rule: Dict):
        """Marca que se requiere aprobación de supervisor"""
        self.facts['requiere_aprobacion'] = True
        self.facts['aprobacion_motivo'] = rule.get('name', 'Regla del sistema experto')

def test_inference_engine():
    """Función de prueba del motor de inferencia"""
    
    # Crear hechos de prueba
    test_facts = {
        'motivo': 'ART',
        'duracion': 10,
        'certificate_uploaded': False,
        'certificate_deadline': datetime.now() - timedelta(hours=25),
        'validation_status': 'validated',
        'ausencias_ultimo_mes': 2
    }
    
    print("[TEST] Probando motor de inferencia avanzado")
    print("=" * 60)
    
    engine = InferenceEngine()
    result = engine.forward_chaining(test_facts)
    
    print(f"[TIME] Tiempo de ejecucion: {result.execution_time:.3f}s")
    print(f"[RULES] Reglas disparadas: {len(result.steps)}")
    print(f"[CONCLUSIONS] Conclusiones: {result.conclusions}")
    print(f"[ACTIONS] Acciones ejecutadas: {result.actions_taken}")
    
    print("\n[STEPS] Pasos del razonamiento:")
    for i, step in enumerate(result.steps, 1):
        print(f"{i}. {step.rule_name}")
        print(f"   Condición: {step.condition}")
        print(f"   Resultado: {step.condition_result}")
        print(f"   Acción: {step.action}")
        print()

if __name__ == "__main__":
    test_inference_engine()