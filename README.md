# Green Planner

Автоматическое проектирование озеленения территории на основе DXF-геоподосновы.

## Что делает проект

Green Planner принимает DXF-файл с геоподосновой (границы участка, коммуникации, здания, дороги) и автоматически генерирует схему посадок деревьев и кустарников с учётом нормативных ограничений.

**Вход:** DXF + YAML-конфигурация  
**Выход:**
- DXF с новыми слоями посадок (исходные слои не изменяются)
- `interpretation.json` — объяснение каждой посадки
- `run_report.json` — отчёт о выполнении

## Архитектура

```
DXF → Reader → Classification → Buffers → Allowed Area
  → Candidate Grid → Greedy Optimization → Validation
  → Interpretation → DXF Writer → JSON Reports
```

Подробнее: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Web UI

```bash
# Terminal 1 — Backend API
source .venv/bin/activate
uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 → click **Try demo dataset** for instant demo.

## Установка

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cd frontend && npm install
```

## Docker

```bash
docker build -t green-planner .

docker run --rm \
  -v ./data:/app/data \
  -v ./config:/app/config \
  green-planner \
  process \
  --input /app/data/input/test.dxf \
  --output /app/data/output/result.dxf \
  --config /app/config/default.yaml
```

## Тестовые DXF

В репозитории **нет реальных DXF от организаторов** — только синтетические:

| Файл | Описание |
|------|----------|
| `data/input/test.dxf` | Простой участок 100×100 м |
| `data/input/synthetic_complex.dxf` | Сложный участок 200×150 м, 3 коммуникации, 2 здания |

```bash
python scripts/create_test_dxf.py
python scripts/create_complex_dxf.py
```

Для финальной демонстрации положите реальный DXF в `data/input/` и настройте слои в `config/default.yaml`.

## Пример запуска

```bash
# Создать тестовые DXF
python scripts/create_test_dxf.py
python scripts/create_complex_dxf.py

# Инспекция входного файла
green-planner inspect --input data/input/test.dxf

# Основная обработка
green-planner process \
  --input data/input/test.dxf \
  --output data/output/result.dxf \
  --config config/default.yaml

# Валидация результата
green-planner validate --input data/output/result.dxf

# Просмотр интерпретации
green-planner report --input data/output/interpretation.json

# Debug-визуализация
green-planner debug \
  --input data/input/test.dxf \
  --output data/output/debug.png
```

## Формат входных данных

DXF-файл (AutoCAD R2010+) с объектами на слоях:

| Категория | Примеры слоёв | Типы объектов |
|-----------|---------------|---------------|
| Граница участка | SITE, BOUNDARY | LWPOLYLINE, POLYLINE |
| Коммуникации | PIPE, WATER, GAS | LINE, LWPOLYLINE |
| Здания | BUILDINGS, BUILDING | LWPOLYLINE |
| Дороги | ROADS, ROAD | LINE, LWPOLYLINE |

Названия слоёв настраиваются в `config/default.yaml`.

## Формат output

### result.dxf
Исходный DXF + новые слои:
- `PLANTING_PROPOSED` — все посадки (POINT)
- `PLANTING_TREES` — деревья (CIRCLE)
- `PLANTING_SHRUBS` — кустарники (CIRCLE)

### interpretation.json
```json
{
  "plantings": [{
    "id": "tree_001",
    "type": "tree",
    "x": 15.0, "y": 20.0,
    "status": "accepted",
    "checks": [{
      "rule": "communication_distance",
      "value": 30.0,
      "required": 2.0,
      "status": "passed",
      "regulation": "743-ПП",
      "clause": "TODO_VERIFY"
    }],
    "explanation": "Посадка типа tree допустима: ..."
  }]
}
```

## Конфигурация

Основной файл: `config/default.yaml`

```yaml
layers:
  communications: [PIPE, WATER, GAS]
  boundary: [SITE]

planting:
  tree:
    enabled: true
    min_spacing: 6.0
    candidate_grid_step: 3.0

rules:
  tree:
    communication:
      minimum_distance: 2.0
      regulation:
        document: "743-ПП"
        clause: "TODO_VERIFY"
```

## Нормативная логика

Нормативные расстояния вынесены в конфигурацию. Неподтверждённые пункты помечены `TODO_VERIFY`.  
Подробнее: [docs/NORMATIVE_LOGIC.md](docs/NORMATIVE_LOGIC.md)

## Ограничения MVP

- Алгоритмический (не ML) подход
- Регулярная сетка кандидатных точек
- Greedy-оптимизация
- 2D-геометрия (без рельефа)
- Нормативные пункты требуют верификации экспертом
- Нет веб-интерфейса

## Известные проблемы

- При отсутствии слоя границы используется convex hull всех объектов
- Сложные MultiPolygon могут замедлять обработку больших файлов
- ARC представляется как полный круг (упрощение для MVP)

## Плотность посадок

`run_report.json` содержит метрики:

- `site_area_m2`, `forbidden_area_m2`, `allowed_area_m2`
- `planting_count`, `density_per_1000m2`
- `planting_config` — min_spacing, max_count, target_density

Ограничение количества через config:

```yaml
planting:
  tree:
    max_count: 50        # жёсткий лимит
    target_density: 5.0  # растений на 1000 м²
```

## Нормативная верификация

См. [docs/NORMATIVE_VERIFICATION.md](docs/NORMATIVE_VERIFICATION.md)

## Docker

См. [docs/DOCKER_TEST.md](docs/DOCKER_TEST.md) — инструкция проверки на Linux.

## Тестирование

```bash
pytest -v   # 32 tests
```

## Лицензия

MIT
