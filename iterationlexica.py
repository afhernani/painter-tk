# Importamos el módulo de expresiones regulares para hacer coincidir patrones de texto
import re

# ============================================================================
# CLASE: PeekableStream
# Propósito: Envuelve un iterador permitiendo "mirar" el siguiente elemento
#            sin consumirlo (técnica "peek")
# ============================================================================
class PeekableStream:
    """
    Clase que permite iterar sobre una secuencia de caracteres
    con capacidad de ver el siguiente elemento sin avanzarlo.
    Útil para analizadores léxicos que necesitan mirar adelante.
    """
    
    def __init__(self, iterator):
        """
        Constructor de la clase.
        
        Args:
            iterator: Cualquier objeto iterable (string, lista, etc.)
        """
        # Convertimos el iterable en un iterador usando iter()
        self.iterator = iter(iterator)
        # Llenamos self.next con el primer elemento
        self._fill()
    
    def _fill(self):
        """
        Método privado que rellena el atributo self.next
        con el siguiente elemento del iterador.
        """
        try:
            # Obtenemos el siguiente elemento del iterador
            self.next = next(self.iterator)
        except StopIteration:
            # Si el iterador se agotó, asignamos None (fin de secuencia)
            self.next = None
    
    def move_next(self):
        """
        Avanza al siguiente elemento y devuelve el actual.
        
        Returns:
            El elemento actual antes de avanzar, o None si está al final.
        """
        # Guardamos el elemento actual
        ret = self.next
        # Rellenamos self.next con el siguiente elemento
        self._fill()
        # Devolvemos el elemento que estaba antes de avanzar
        return ret


# ============================================================================
# FUNCIÓN: _scan_string
# Propósito: Lee una cadena delimitada por comillas (simples o dobles)
# ============================================================================
def _scan_string(delim, chars):
    """
    Escanea una cadena de texto delimitada por un carácter específico.
    
    Args:
        delim: Carácter delimitador (generalmente "'" o '"')
        chars: Objeto PeekableStream con los caracteres restantes
    
    Returns:
        La cadena de texto sin los delimitadores
    
    Raises:
        Exception: Si no encuentra el delimitador de cierre
    """
    # Inicializamos una cadena vacía para acumular el contenido
    ret = ""
    
    # Mientras el siguiente carácter NO sea el delimitador de cierre
    while chars.next != delim:
        # Avanzamos y obtenemos el siguiente carácter
        c = chars.move_next()
        
        # Si llegamos al final sin encontrar el delimitador
        if c is None:
            raise Exception("A string ran off the end of the program.")
        
        # Añadimos el carácter a la cadena acumulada
        ret += c
    
    # Consumimos el delimitador final (lo descartamos)
    chars.move_next()
    
    # Devolvemos la cadena leída
    return ret


# ============================================================================
# FUNCIÓN: _scan
# Propósito: Escanea una secuencia de caracteres que coinciden con un patrón
# ============================================================================
def _scan(first_char, chars, allowed):
    """
    Escanea una secuencia de caracteres que coinciden con una expresión regular.
    
    Args:
        first_char: Primer carácter ya leído (siempre se incluye)
        chars: Objeto PeekableStream con los caracteres restantes
        allowed: Expresión regular que define los caracteres permitidos
    
    Returns:
        La secuencia completa de caracteres que coinciden con el patrón
    """
    # Inicializamos el resultado con el primer carácter
    ret = first_char
    
    # Obtenemos el siguiente carácter sin consumirlo (peek)
    p = chars.next
    
    # Mientras haya siguiente carácter Y coincida con el patrón permitido
    while p is not None and re.match(allowed, p):
        # Añadimos el carácter y avanzamos
        ret += chars.move_next()
        # Actualizamos p con el nuevo siguiente carácter
        p = chars.next
    
    # Devolvemos la secuencia escaneada
    return ret


# ============================================================================
# FUNCIÓN PRINCIPAL: lex
# Propósito: Analizador léxico (lexer) que convierte texto en tokens
# ============================================================================
def lex(chars_iter):
    """
    Función generadora que convierte un iterable de caracteres en una
    secuencia de tokens (unidades léxicas con tipo y valor).
    
    Args:
        chars_iter: Iterable de caracteres (string, lista, etc.)
    
    Yields:
        Tuplas (tipo, valor) donde:
            - tipo: Categoría del token ("number", "symbol", "operation", etc.)
            - valor: El contenido real del token
    
    Tokens reconocidos:
        - Espacios en blanco: Se ignoran
        - Caracteres especiales: (),{},;=:
        - Operadores: +, -, *, /
        - Identificadores SVG: M, A, L, S
        - Cadenas: Entre comillas simples o dobles
        - Números: Secuencias de dígitos y puntos
        - Símbolos: Identificadores alfanuméricos
    """
    # Creamos un PeekableStream para poder mirar adelante
    chars = PeekableStream(chars_iter)
    
    # Mientras haya caracteres por procesar
    while chars.next is not None:
        # Obtenemos el siguiente carácter
        c = chars.move_next()
        
        # ================================================================
        # CASO 1: Espacios en blanco (espacio y salto de línea)
        # ================================================================
        if c in " \n":
            pass  # Ignoramos espacios en blanco
        
        # ================================================================
        # CASO 2: Caracteres especiales de puntuación
        # ================================================================
        elif c in "(){},;=:":
            # Devolvemos el carácter como token especial
            yield (c, " ")
        
        # ================================================================
        # CASO 3: Operadores aritméticos
        # ================================================================
        elif c in "+-*/":
            # Clasificamos como operación
            yield ("operation", c)
        
        # ================================================================
        # CASO 4: Comandos SVG path (M=move, A=arc, L=line, S=smooth)
        # ================================================================
        elif c in "MALS":
            # Clasificamos como identificador de comando SVG
            yield ("identificador", c)
        
        # ================================================================
        # CASO 5: Cadenas de texto entre comillas
        # ================================================================
        elif c in ("'", '"'):
            # Escaneamos la cadena completa hasta el delimitador
            yield ("string", _scan_string(c, chars))
        
        # ================================================================
        # CASO 6: Números (dígitos y punto decimal)
        # ================================================================
        elif re.match("[.0-9]", c):
            # Escaneamos el número completo (ej: "34.6", "123", ".5")
            yield ("number", _scan(c, chars, "[.0-9]"))
        
        # ================================================================
        # CASO 7: Símbolos/identificadores (letras, números, guión bajo)
        # ================================================================
        elif re.match("[_a-zA-Z]", c):
            # Escaneamos el identificador completo (ej: "variable1", "_x")
            yield ("symbol", _scan(c, chars, "[_a-zA-Z0-9]"))
        
        # ================================================================
        # CASO 8: Tabuladores (no permitidos)
        # ================================================================
        elif c == "\t":
            raise Exception("Tabs are not allowed in Cell.")
        
        # ================================================================
        # CASO 9: Caracteres no reconocidos
        # ================================================================
        else:
            raise Exception("Unexpected character: '" + c + "'.")


# ============================================================================
# BLOQUE DE PRUEBAS
# Se ejecuta solo si el archivo se ejecuta directamente (no importado)
# ============================================================================
if __name__ == '__main__':
    # Prueba 1: Imprimir el generador (muestra objeto, no los tokens)
    print(lex('() "hola mundo", 2 + 3, M23.4,50.7'))
    
    # Prueba 2: Iterar sobre los tokens de un comando SVG path
    # Este es un ejemplo típico: "M34.6,67.12 0 0 0 0 A"
    # Significa: Move to (34.6,67.12), luego parámetros, luego Arc
    for l in lex('M34.6,67.12 0 0 0 0 A'):
        print(l)
    
    # Prueba 3: Ejemplo más complejo con expresiones
    for l in lex('M34.6,67.12 0 0 0 0 (0.1 + 0.3), CXAx'):
        print(l)