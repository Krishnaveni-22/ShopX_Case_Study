CREATE DATABASE IF NOT EXISTS shopxdw;
USE shopxdw;

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(30) PRIMARY KEY,
    customer_name VARCHAR(100),
    country VARCHAR(10),
    region VARCHAR(50),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    street_address VARCHAR(255),
    phone_number VARCHAR(50),
    email_address VARCHAR(150),
    language_code VARCHAR(10),
    tax_number VARCHAR(50),
    customer_group INT,
    sales_organization INT,
    distribution_channel INT,
    division INT
);

CREATE TABLE IF NOT EXISTS carriers (
    carrier_id VARCHAR(30) PRIMARY KEY,
    carrier_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id BIGINT PRIMARY KEY,
    customer_id VARCHAR(30) NOT NULL,
    order_date DATE,
    order_type VARCHAR(20),
    sales_organization INT,
    distribution_channel INT,
    division INT,
    order_status VARCHAR(30),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id BIGINT,
    item_number INT,
    product_id VARCHAR(50),
    order_quantity DECIMAL(18,2),
    unit_price DECIMAL(18,2),
    item_status VARCHAR(30),
    expected_delivery_date DATE,
    PRIMARY KEY (order_id, item_number),
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    delivery_id BIGINT,
    carrier_id VARCHAR(30),
    shipment_date DATE,
    shipping_point VARCHAR(30),
    shipment_status VARCHAR(30),
    route INT,
    shipping_type VARCHAR(30),
    customer_id VARCHAR(30),
    CONSTRAINT fk_shipments_order FOREIGN KEY (order_id)
        REFERENCES orders(order_id),
    CONSTRAINT fk_shipments_carrier FOREIGN KEY (carrier_id)
        REFERENCES carriers(carrier_id)
);

CREATE TABLE IF NOT EXISTS shipment_items (
    shipment_id BIGINT,
    item_number INT,
    product_id VARCHAR(50),
    shipped_quantity DECIMAL(18,2),
    item_status VARCHAR(30),
    delivery_id BIGINT,
    customer_id VARCHAR(30),
    order_id BIGINT,
    sales_item INT,
    shipment_date DATE,
    PRIMARY KEY (shipment_id, item_number)
);

CREATE TABLE IF NOT EXISTS delivery_analytics (
    order_id BIGINT PRIMARY KEY,
    customer_id VARCHAR(30),
    carrier_id VARCHAR(30),
    order_date DATE,
    shipment_date DATE,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    order_processing_days INT,
    delivery_time_days INT,
    delivery_delay_days INT,
    on_time_flag TINYINT,
    delay_reason VARCHAR(100)
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_shipments_order ON shipments(order_id);
CREATE INDEX idx_delivery_customer ON delivery_analytics(customer_id);
CREATE INDEX idx_delivery_carrier ON delivery_analytics(carrier_id);
CREATE INDEX idx_delivery_order_date ON delivery_analytics(order_date);
USE shopx_dw;

show tables;





SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM orders;
SELECT COUNT(*) FROM order_items;
SELECT COUNT(*) FROM shipments;
SELECT COUNT(*) FROM shipment_items;
SELECT COUNT(*) FROM delivery_analytics;

commit;


SELECT
    AVG(order_processing_days) AS avg_processing_days
FROM delivery_analytics;

SELECT
    COUNT(*) AS late_orders
FROM delivery_analytics
WHERE delivery_delay_days > 0;

SELECT
    COUNT(*) AS late_orders
FROM delivery_analytics
WHERE delivery_delay_days > 0;

SELECT
    carrier_id,
    AVG(delivery_delay_days) AS avg_delay
FROM delivery_analytics
GROUP BY carrier_id;

COMMIT;

USE shopx_dw;
SELECT COUNT(*) FROM customers;