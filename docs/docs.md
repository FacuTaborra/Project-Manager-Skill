# PM Skill — Por qué tu equipo debería usarla

## El problema

Cuando tenés a Claude Code abierto en un repo, hay dos cosas que hacés todo el tiempo que se vuelven fricción:

1. **Saber qué hay pendiente.** Tenés que abrir el browser, ir a Linear o ClickUp, navegar al proyecto correcto, leer los tickets. Tardás 2 minutos en orientarte.
2. **Crear issues bien escritas.** Cuando planificás una feature, alguien tiene que hacer el trabajo de bajar eso a tickets concretos con descripción, criterios de aceptación, y contexto técnico. Si lo hacés a mano, es lento. Si no lo hacés, los tickets quedan a medias.

La PM Skill le da a Claude contexto directo de tu tracker y le permite crear issues sin que salgas del editor.

---

## Cómo se usa

Abrís Claude Code en cualquier repo del equipo y escribís:

```
/pm
```

Claude lee el estado actual de tu proyecto en Linear (o ClickUp) y te responde algo así:

```
## PM Briefing — alerts-api
📅 2026-05-18

### 🔴 Bloqueado
- ALR-42: Deploy falla en prod por variable de entorno missing

### 🔵 En progreso
- ALR-38: Migración a nuevo schema de alertas
- ALR-39: Rate limiting por tenant

### 📋 Próximos (top 5)
- ALR-40: Endpoint de health check
- ALR-41: Dashboard de métricas
```

En 10 segundos sabés dónde está el proyecto. Sin abrir el browser.

---

Si en cambio querés planificar algo nuevo:

```
/pm agreguemos soporte para webhooks salientes
```

Claude busca duplicados en el tracker, propone un tablero de hasta 8 issues con título, tipo, estado inicial y descripción breve, y **espera tu confirmación antes de crear nada**. Si confirmás, crea todos los tickets en Linear/ClickUp con descripción estructurada (objetivo, criterios de aceptación, contexto técnico).

---

## Por qué no simplemente usar MCP

MCP (Model Context Protocol) es la forma "oficial" de conectar Claude con herramientas externas. Linear y ClickUp tienen sus propios MCP servers. Entonces la pregunta obvia es: ¿por qué no usar eso directamente?

### 1. MCP no tiene memoria entre llamadas

Cada vez que Claude necesita saber tu team ID, project ID, o los estados disponibles, MCP hace una llamada a la API. Si en una sesión necesitás briefing + crear 5 issues, son decenas de llamadas redundantes.

La skill tiene un **cache local** (`.linear-cache.json` / `.clickup-cache.json`). Después del primer uso, las llamadas de discovery desaparecen. Es instantáneo.

### 2. MCP no tiene contexto del repo

MCP no sabe en qué repo estás trabajando. Tenés que decirle explícitamente a Claude qué proyecto de Linear corresponde a qué carpeta.

La skill **auto-detecta el repo** desde el directorio donde corrés Claude Code y lo mapea al proyecto correspondiente en el tracker. Abrís Claude en `alerts-api/` y ya sabe de qué proyecto hablar.

### 3. MCP te da acceso crudo, no inteligencia

Con MCP, Claude tiene herramientas para hacer llamadas individuales a la API. Pero decidir cuándo usarlas, en qué orden, y cómo interpretar los resultados queda librado a la creatividad de Claude en cada sesión.

La skill tiene un **contrato estricto**: Claude solo puede ejecutar los subcomandos documentados (`briefing`, `create-issue`, `search`, etc.), en un flujo definido. El comportamiento es predecible y consistente entre sesiones y entre desarrolladores del equipo.

### 4. Multi-provider sin duplicar configuración

Si el equipo usa Linear para eng y ClickUp para producto, podés configurar cada repo con su provider. La skill resuelve el provider correcto automáticamente por repo, usando el mismo `/pm` en todos lados.

Con MCP tendrías que configurar y mantener dos MCP servers separados con sus propias rutas de autenticación.

---

## Qué puede hacer


| Comando                                                     | Qué hace                                             |
| ----------------------------------------------------------- | ---------------------------------------------------- |
| `/pm`                                                       | Briefing: qué está abierto, en progreso, bloqueado   |
| `/pm <descripción de feature>`                              | Propone un tablero de issues y las crea al confirmar |
| "buscá si ya existe un ticket sobre X"                      | Busca duplicados en el tracker                       |
| "asigná ALR-42 a [juan@equipo.com](mailto:juan@equipo.com)" | Actualiza assignee de una issue existente            |
| "pasá ALR-38 a In Review"                                   | Cambia el estado de una issue                        |
| "creá un doc en ClickUp con el ADR de esta decisión"        | Crea documentación directamente en ClickUp           |


---

## Cómo se instala

Cada desarrollador instala la skill una sola vez:

```bash
git clone https://github.com/FacuTaborra/product-manager-skill.git
cd product-manager-skill

# Linux / macOS
./install.sh

# Windows
.\install.ps1
```

El installer crea un enlace desde `~/.claude/skills/pm/` al repo clonado y configura los permisos necesarios en Claude Code. Después, cualquier `git pull` actualiza la skill automáticamente — no hay que reinstalar.

El único paso manual es poner tu API key personal de Linear o ClickUp en `~/.claude/secrets/`:

```
LINEAR_API_KEY=lin_api_xxxxxxxx
```

Cada dev usa su propia key. No hay secretos compartidos.

Verificás que todo está bien con:

```bash
pm doctor
```

---

## Arquitectura (para los curiosos)

La skill es un CLI de Python puro — sin dependencias externas, solo stdlib. Sigue arquitectura hexagonal: el dominio no sabe nada de HTTP ni de qué tracker estás usando. Agregar un nuevo provider (GitHub Issues, Jira) es implementar un Protocol de ~10 métodos y registrarlo.

El flujo cuando escribís `/pm`:

```
Claude Code
  └── lee SKILL.md (instrucciones para Claude)
       └── Claude ejecuta: python3 ~/.claude/skills/pm/pm.py briefing
            └── CLI lee cache → llama API si hace falta → imprime JSON
                 └── Claude parsea JSON y presenta el briefing en tu idioma
```

Claude nunca improvisa cómo hablar con la API. Solo interpreta el JSON que el CLI le devuelve.

---

## Preguntas frecuentes

**¿Funciona si el equipo usa Linear y yo uso ClickUp?**
Sí. El provider se configura por repo en un archivo `projects.pm`. Cada dev apunta al tracker correcto para cada proyecto.

**¿Claude puede hacer cosas que no quiero sin pedirme permiso?**
No. La skill nunca crea ni modifica nada sin que el usuario confirme explícitamente. El briefing es solo lectura. El plan de issues se muestra primero y se crea solo después de tu "sí".

**¿Qué pasa si el proyecto de Linear no se llama igual que el repo?**
Podés configurar el ID explícitamente con `pm setup --project-id <id>`, o declararlo en el archivo `projects.pm` del repo.

**¿Los tickets que crea Claude son buenos?**
Depende del contexto que le des. Si le decís "agreguemos webhooks salientes", va a generar issues razonables. Si además tenés un vault de Obsidian con notas del proyecto, Claude las lee y genera issues con contexto real del codebase. Siempre podés editar la propuesta antes de confirmar.