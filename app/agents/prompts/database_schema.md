# Esquema de Base de Datos — NovaMart Level 1

## Diagrama de relaciones

```
regions (4 filas)
  └── customers.region_id (puede ser NULL)

categories (4 filas)
  └── products.category_id

customers (200 filas)
  └── orders.customer_id

products (30 filas)
  └── order_items.product_id

orders (~2,000 filas)
  └── order_items.order_id
```

## Tablas

### regions
| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | SERIAL PK | Identificador unico |
| name | VARCHAR(100) | Nombre de la region (unico) |

### categories
| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | SERIAL PK | Identificador unico |
| name | VARCHAR(100) | Nombre de la categoria (unico) |

### products
| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | SERIAL PK | Identificador unico |
| name | VARCHAR(200) | Nombre del producto |
| category_id | INT FK | Referencia a categories.id |
| price | NUMERIC(10,2) | Precio en USD |
| is_active | BOOLEAN | Si el producto esta activo (default TRUE) |

### customers
| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | SERIAL PK | Identificador unico |
| name | VARCHAR(200) | Nombre completo |
| email | VARCHAR(255) | Email (unico) |
| region_id | INT FK (nullable) | Referencia a regions.id — puede ser NULL |
| created_at | DATE | Fecha de registro |

### orders
| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | SERIAL PK | Identificador unico |
| customer_id | INT FK | Referencia a customers.id |
| order_date | DATE | Fecha del pedido |
| status | VARCHAR(20) | Estado: 'delivered', 'shipped', o 'cancelled' |
| total_amount | NUMERIC(10,2) | Monto total del pedido en USD |

### order_items
| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | SERIAL PK | Identificador unico |
| order_id | INT FK | Referencia a orders.id |
| product_id | INT FK | Referencia a products.id |
| quantity | INT | Cantidad de unidades |
| unit_price | NUMERIC(10,2) | Precio unitario al momento de la compra |
| line_total | NUMERIC(10,2) | Total de la linea (quantity * unit_price) |
