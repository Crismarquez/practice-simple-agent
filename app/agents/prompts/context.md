# Contexto de Negocio — NovaMart E-Commerce (Simplificado)

> Este documento describe el dominio de negocio detras de la base de datos que tu agente consultara.

---

## Acerca de NovaMart

NovaMart es una tienda de comercio electronico que vende productos de consumo en cuatro categorias: **Electronics**, **Home & Garden**, **Clothing** y **Sports**.

La base de datos contiene datos transaccionales del **ano 2024** (enero a diciembre). Todas las transacciones estan en **USD**.

---

## Regiones

NovaMart organiza sus clientes en cuatro regiones:

- **North America** — mercado principal (~40%)
- **Europe** — segundo mercado (~30%)
- **Asia Pacific** — tercer mercado (~20%)
- **Latin America** — mercado emergente (~10%)

Nota: algunos clientes (~5%) no tienen region asignada.

---

## Catalogo de productos

NovaMart vende **30 productos** distribuidos en las 4 categorias. Cada producto tiene un precio fijo en USD.

---

## Pedidos

Un pedido puede tener uno de estos estados:

| Estado | Significado |
|--------|------------|
| **delivered** | Entregado exitosamente al cliente (~85%) |
| **shipped** | En camino al cliente (~5%) |
| **cancelled** | Cancelado, no se completo (~10%) |

### Reglas de negocio

- **Los pedidos cancelados NO se cuentan como ventas** en los reportes estandar.
- Cada pedido tiene un `total_amount` que representa el monto total cobrado.
- La definicion de **"ingreso" (revenue)** es la suma de `total_amount` de pedidos no cancelados.

---

## Estructura de la base de datos

La base de datos tiene **6 tablas**:

| Tabla | Descripcion | Filas aprox. |
|-------|-------------|-------------|
| **regions** | Regiones de clientes | 4 |
| **categories** | Categorias de productos | 4 |
| **products** | Catalogo de productos | 30 |
| **customers** | Clientes registrados | 200 |
| **orders** | Pedidos realizados | ~2,000 |
| **order_items** | Lineas de detalle por pedido | ~5,000 |

### Relaciones

- `products.category_id` → `categories.id`
- `customers.region_id` → `regions.id` (puede ser NULL)
- `orders.customer_id` → `customers.id`
- `order_items.order_id` → `orders.id`
- `order_items.product_id` → `products.id`

---

## Glosario

| Termino | Definicion |
|---------|-----------|
| **Ingreso (Revenue)** | Suma de `total_amount` de pedidos no cancelados |
| **Pedido valido** | Un pedido con status diferente de 'cancelled' |
| **Producto mas vendido** | El producto con mas unidades vendidas (suma de `quantity` en pedidos validos) |
| **Valor promedio del pedido** | Promedio de `total_amount` de pedidos validos |
