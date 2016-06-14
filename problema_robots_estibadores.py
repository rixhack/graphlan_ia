import problema_planificación as probpl

# Clases de símbolos de objetos
Localizaciones = ['1','2','3','4','5','6']
Robots = ['R1']
Contenedores = ['A','B','C']
Grúas = ['G1','G2']

# Variables de estados
carga_robot = probpl.VariableDeEstados(nombre='carga_robot({r})', r=Robots)
contenedor_debajo = probpl.VariableDeEstados(nombre='contenedor_debajo({c})', c=Contenedores)
superior = probpl.VariableDeEstados(nombre='superior({l})',l=Localizaciones)

# Relaciones rígidas
adyacentes = probpl.RelaciónRígida(lambda l1, l2: (abs(int(l1)-int(l2))==3) or (abs(int(l1)-int(l2))==1 and max(int(l1),int(l2))!=7 and max(int(l1),int(l2)!=4)))
puede_operar = probpl.RelaciónRígida(lambda g, l: (g=='G1' and int(l)<4) or (g=='G2' and int(l)>3))

# Operadores
mover_robot = probpl.Operador(
  nombre='mover_robot({r},{l1},{l2})',
  precondiciones=[superior({'{l1}':'{r}'}),
                  superior({'{l2}':'ninguno'})],
  efectos=[superior({'{l2}':'{r}'}),
           superior({'{l1}':'ninguno'})],
  relaciones_rígidas=adyacentes('{l1}','{l2}'),
  r=Robots,
  l1=Localizaciones,
  l2=Localizaciones
)

cargar_robot = probpl.Operador(
  nombre='cargar_robot({c},{r},{g},{l1},{l2})',
  precondiciones=[superior({'{l2}':'{r}'}),
                  superior({'{l1}':'{c}'}),
                  carga_robot({'{r}':'ninguno'}),
                  contenedor_debajo({'{c}':'ninguno'})],
  efectos=[carga_robot({'{r}':'{c}'}),
           superior({'{l1}':'ninguno'})],
  relaciones_rígidas=[puede_operar('{g}','{l1}'),puede_operar('{g}','{l2}')],
  c=Contenedores,
  r=Robots,
  g=Grúas,
  l1=Localizaciones,
  l2=Localizaciones
)

cargar_pila_robot = probpl.Operador(
  nombre='cargar_pila_robot({c1},{c2},{r},{g},{l1},{l2})',
  precondiciones=[superior({'{l2}':'{r}'}),
                  superior({'{l1}':'{c1}'}),
                  carga_robot({'{r}':'ninguno'}),
                  contenedor_debajo({'{c1}':'{c2}'})],
  efectos=[carga_robot({'{r}':'{c1}'}),
           superior({'{l1}':'{c2}'}),
           contenedor_debajo({'{c1}':'ninguno'})],
  relaciones_rígidas=[puede_operar('{g}','{l1}'),puede_operar('{g}','{l2}')],
  c1=Contenedores,
  c2=Contenedores,
  r=Robots,
  g=Grúas,
  l1=Localizaciones,
  l2=Localizaciones
)

descargar_robot = probpl.Operador(
  nombre='descargar_robot({c},{r},{g},{l1},{l2})',
  precondiciones=[superior({'{l1}':'{r}'}),
                  carga_robot({'{r}':'{c}'}),
                  superior({'{l2}':'ninguno'})],
  efectos=[carga_robot({'{r}':'ninguno'}),
           superior({'{l2}':'{c}'})],
  relaciones_rígidas=[puede_operar('{g}','{l1}'),puede_operar('{g}','{l2}')],
  c=Contenedores,
  r=Robots,
  g=Grúas,
  l1=Localizaciones,
  l2=Localizaciones
)

descargar_robot_en_pila = probpl.Operador(
  nombre='descargar_robot_en_pila({c1},{c2},{r},{g},{l1},{l2})',
  precondiciones=[superior({'{l1}':'{r}'}),
                  carga_robot({'{r}':'{c1}'}),
                  superior({'{l2}':'{c2}'})],
  efectos=[carga_robot({'{r}':'ninguno'}),
           superior({'{l2}':'{c1}'}),
           contenedor_debajo({'{c1}':'{c2}'})],
  relaciones_rígidas=[puede_operar('{g}','{l1}'),puede_operar('{g}','{l2}')],
  c1=Contenedores,
  c2=Contenedores,
  r=Robots,
  g=Grúas,
  l1=Localizaciones,
  l2=Localizaciones
)

mover_contenedor = probpl.Operador(
  nombre='mover_contenedor({c},{g},{l1},{l2})',
  precondiciones=superior({'{l1}':'{c}'}),
  efectos=superior({'{l2}':'{c}'}),
  relaciones_rígidas=[puede_operar('{g}','{l1}'),puede_operar('{g}','{l2}')],
  c=Contenedores,
  g=Grúas,
  l1=Localizaciones,
  l2=Localizaciones
)

# Instancia del problema
problema_robots_estibadores = probpl.ProblemaPlanificación(
  operadores=[mover_robot, cargar_robot, descargar_robot, cargar_pila_robot, descargar_robot_en_pila],#, mover_contenedor],
  estado_inicial = probpl.Estado(superior({'6':'R1',
                                           '1':'C',
                                           '2':'ninguno',
                                           '3':'ninguno',
                                           '4':'ninguno',
                                           '5':'ninguno'}),
                                 carga_robot({'R1':'ninguno'}),
                                 contenedor_debajo({'A':'ninguno',
                                                    'B':'A',
                                                    'C':'B'})),
  objetivos=[superior({'6':'C','5':'R1','4':'ninguno','3':'ninguno','2':'ninguno','1':'ninguno'}),contenedor_debajo({'A':'ninguno','B':'A','C':'B'})]
)

##### Funciones para calcular la heurística ######
def coordenadas(pos):
  x = pos%3
  if x==0:
    x=3
  y = pos//4+1
  return (x,y)

def distancia(pos1,pos2):
  (x1,y1) = coordenadas(int(pos1))
  (x2,y2) = coordenadas(int(pos2))
  return abs(x2-x1)+abs(y2-y1)

def pos_actual(nodo,c):
  for l in Localizaciones:
    s = nodo.estado.variables_estados['superior({l})'][l]
    if s==c:
      return l
    elif s=='ninguno':
      continue
    else:
      for r in Robots:
        if s==r and nodo.estado.variables_estados['carga_robot({r})'][r]==c:
          return l
      for con in Contenedores:
        if s==con:
          cd = nodo.estado.variables_estados['contenedor_debajo({c})'][con]
          while cd!='ninguno':
            if cd == c:
              return l
            else:
              cd = nodo.estado.variables_estados['contenedor_debajo({c})'][cd]

def pos_objetivo(c):
  for l in Localizaciones:
    s = problema_robots_estibadores.objetivos[0][l]
    if s==c:
      return l
    elif s=='ninguno':
      continue
    else:
      for con in Contenedores:
        if s==con:
          cd = problema_robots_estibadores.objetivos[1][con]
          while cd!='ninguno':
            if cd == c:
              return l
            cd = problema_robots_estibadores.objetivos[1][cd]

    

### Búsqueda de soluciones ###


import búsqueda_espacio_estados as búsquee

# búsqueda_profundidad = búsquee.BúsquedaEnProfundidad()
# print(búsqueda_profundidad.buscar(problema_robots_estibadores))
búsqueda_anchura = búsquee.BúsquedaEnAnchura()
print(búsqueda_anchura.buscar(problema_robots_estibadores))

def f(nodo):
  v = 0
  for c in Contenedores:
    v=v+distancia(pos_actual(nodo,c),pos_objetivo(c))
  return v

def h(nodo):
  return 0
# búsqueda_primero = búsquee.BúsquedaPrimeroElMejor(f)
# print(búsqueda_primero.buscar(problema_robots_estibadores))
# búsqueda_aestrella = búsquee.BúsquedaAEstrella(h)
# print(búsqueda_aestrella.buscar(problema_robots_estibadores))

      
      

