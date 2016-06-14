import re
import itertools
import copy
import problema_espacio_estados as probee


class VariableDeEstados(dict):
    def __init__(self, nombre, **dominios):
        self.nombre = nombre
        self.variables = re.findall('{(.+?)}', nombre)
        self.dominios = [dominios[variable] for variable in self.variables]

    def _es_parámetro(self, valor):
        return isinstance(valor, str) and valor.startswith('{') and valor.endswith('}')

    def __setitem__(self, valores_dominios, valor_variable):
        if not isinstance(valores_dominios, tuple):
            self[tuple(valores_dominios)] = valor_variable
        elif all(self._es_parámetro(valor) or valor in dominio
                 for valor, dominio in zip(valores_dominios, self.dominios)):
            super().__setitem__(valores_dominios, valor_variable)
        else:
            raise KeyError('Valores fuera del dominio de la variable de estados')

    def __getitem__(self, valores_dominios):
        if not isinstance(valores_dominios, tuple):
            return self[(valores_dominios,)]
        elif all(self._es_parámetro(valor) or valor in dominio
                 for valor, dominio in zip(valores_dominios, self.dominios)):
            return super().__getitem__(valores_dominios)
        else:
            raise KeyError('Valores fuera del dominio de la variable de estados')

    def __call__(self, asignaciones):
        nueva_instancia = copy.deepcopy(self)
        if not isinstance(asignaciones, dict):
            asignaciones = {(): asignaciones}
        for valores_dominios, valor_variable in asignaciones.items():
            if not isinstance(valores_dominios, tuple):
                valores_dominios = (valores_dominios,)
            if len(valores_dominios) == len(self.variables):
                nueva_instancia[valores_dominios] = valor_variable
            else:
                raise KeyError('Número insuficiente de valores del dominio')
        return nueva_instancia

    def __eq__(self, otro):
        return (self.nombre == otro.nombre and
                all(set(dominio1) == set(dominio2)
                    for dominio1, dominio2 in zip(self.dominios, otro.dominios)) and
                super().__eq__(otro))

    # def __eq__(self, otro):
    #     if not (len(self.variables) == len(otro.variables) and
    #             all(set(dominio1) == set(dominio2)
    #                 for dominio1, dominio2 in zip(self.dominios, otro.dominios))):
    #         return False
    #     for valores_dominios in itertools.product(*self.dominios):
    #         try:
    #             valor1 = self[valores_dominios]
    #         except KeyError:
    #             valor1 = 'No definido'
    #         try:
    #             valor2 = otro[valores_dominios]
    #         except KeyError:
    #             valor2 = 'No definido'
    #         if not (self.nombre.format(**dict(zip(self.variables, valores_dominios))) ==
    #                 otro.nombre.format(**dict(zip(otro.variables, valores_dominios))) and
    #                 valor1 == valor2):
    #             return False
    #     return True

    def __str__(self):
        valores = []
        for valores_dominios in itertools.product(*self.dominios):
            valor = self.get(valores_dominios, 'No definido')
            valores.append((valores_dominios, valor))
        return '\n'.join(
            (self.nombre + ' = {}').format(valor, **dict(zip(self.variables, valores_dominios)))
            for valores_dominios, valor in valores)

    def es_total(self):
        return all(valores_dominios in self
                   for valores_dominios in itertools.product(*self.dominios))


class Estado:
    def __init__(self, *variables_estados):
        for variable_estados in variables_estados:
            if not variable_estados.es_total():
                raise ValueError(
                    'Variable de estados {} parcialmente definida'.format(variable_estados.nombre))
        self.variables_estados = {variable_estados.nombre: variable_estados
                                  for variable_estados in variables_estados}

    def __eq__(self, otro):
        return (set(self.variables_estados) == set(otro.variables_estados) and
                all(self.variables_estados[nombre] == otro.variables_estados[nombre]
                    for nombre in self.variables_estados))

    def __str__(self):
        return '\n\n'.join(str(variable_estados)
                           for variable_estados in self.variables_estados.values())

    def satisface(self, asignación):
        nombre = asignación.nombre
        return (nombre in self.variables_estados and
                all(valores in self.variables_estados[nombre] and
                    self.variables_estados[nombre][valores] == asignación[valores]
                    for valores in asignación))


class AcciónPlanificación(probee.Acción):
    def __init__(self, nombre='', precondiciones=None, efectos=None, coste=None):
        super().__init__(nombre=nombre, coste=coste)
        if precondiciones is None:
            precondiciones = []
        if not isinstance(precondiciones, list):
            precondiciones = [precondiciones]
        self.precondiciones = precondiciones
        if efectos is None:
            efectos = []
        if not isinstance(efectos, list):
            efectos = [efectos]
        self.efectos = efectos

    def es_aplicable(self, estado):
        return all(estado.satisface(precondición)
                   for precondición in self.precondiciones)

    def aplicar(self, estado):
        nuevo_estado = copy.deepcopy(estado)
        for efecto in self.efectos:
            nombre = efecto.nombre
            variable_estados = nuevo_estado.variables_estados[nombre]
            nuevo_estado.variables_estados[nombre] = variable_estados(efecto)
        return nuevo_estado


class RelaciónRígida:
    def __init__(self, predicado=lambda *argumentos: True):
        self.predicado = predicado

    def verifica(self, asignación):
        return self.predicado(*(argumento.format(**asignación)
                                for argumento in self.argumentos))

    def __call__(self, *argumentos):
        relación_rígida = copy.deepcopy(self)
        relación_rígida.argumentos = argumentos
        return relación_rígida


class Operador:
    def __init__(self, nombre='', precondiciones=None, efectos=None, relaciones_rígidas=None,
                 coste=None, **variables):
        self.nombre = nombre
        if precondiciones is None:
            precondiciones = []
        if not isinstance(precondiciones, list):
            precondiciones = [precondiciones]
        self.precondiciones = precondiciones
        if efectos is None:
            efectos = []
        if not isinstance(efectos, list):
            efectos = [efectos]
        self.efectos = efectos
        if relaciones_rígidas is None:
            relaciones_rígidas = []
        if not isinstance(relaciones_rígidas, list):
            relaciones_rígidas = [relaciones_rígidas]
        self.relaciones_rígidas = relaciones_rígidas
        self.coste = coste
        self.variables = variables

    def _procesar(self, componente, asignación):
        nueva_componente = copy.deepcopy(componente)
        for valores_dominios, valor_variable in nueva_componente.items():
            del nueva_componente[valores_dominios]
            nuevos_valores = tuple(valor.format(**asignación) for valor in valores_dominios)
            nuevo_valor = valor_variable.format(**asignación)
            nueva_componente[nuevos_valores] = nuevo_valor
        return nueva_componente

    def obtener_acción(self, asignación):
        nombre = self.nombre.format(**asignación)
        precondiciones = [self._procesar(precondición, asignación)
                          for precondición in self.precondiciones]
        efectos = [self._procesar(efecto, asignación)
                   for efecto in self.efectos]
        return AcciónPlanificación(nombre, precondiciones, efectos, self.coste)

    def verifica_relaciones_rígidas(self, asignación):
        return all(relación_rígida.verifica(asignación)
                   for relación_rígida in self.relaciones_rígidas)

    def obtener_acciones(self):
        nombres_variables = self.variables.keys()
        valores_variables = self.variables.values()
        producto_valores = itertools.product(*valores_variables)
        asignaciones = (dict(zip(nombres_variables, valores)) for valores in producto_valores)
        return [self.obtener_acción(asignación) for asignación in asignaciones
                if self.verifica_relaciones_rígidas(asignación)]


class ProblemaPlanificación(probee.ProblemaEspacioEstados):
    def __init__(self, operadores, estado_inicial=None, objetivos=None):
        if not isinstance(operadores, list):
            operadores = [operadores]
        if objetivos is None:
            objetivos = []
        if not isinstance(objetivos, list):
            objetivos = [objetivos]
        self.objetivos = objetivos
        acciones = sum((operador.obtener_acciones() for operador in operadores), [])
        super().__init__(acciones, estado_inicial)

    def es_estado_final(self, estado):
        return all(estado.satisface(objetivo)
                   for objetivo in self.objetivos)
