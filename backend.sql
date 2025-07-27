-- Drop existing objects to start fresh
DROP INDEX idx_rentals_user_id;

DROP TABLE Users CASCADE CONSTRAINTS;
DROP TABLE Gear CASCADE CONSTRAINTS;
DROP TABLE Rentals CASCADE CONSTRAINTS;
DROP TABLE Subscriptions CASCADE CONSTRAINTS;
DROP TABLE Payments CASCADE CONSTRAINTS;
DROP TABLE Penalties CASCADE CONSTRAINTS;
DROP TABLE Audit_Log CASCADE CONSTRAINTS;

DROP SEQUENCE users_seq;
DROP SEQUENCE gear_seq;
DROP SEQUENCE rentals_seq;
DROP SEQUENCE subs_seq;
DROP SEQUENCE payments_seq;
DROP SEQUENCE penalties_seq;
DROP SEQUENCE audit_seq;

-- TABLE SCHEMA

CREATE TABLE Users (
    user_id         NUMBER PRIMARY KEY,
    name            VARCHAR2(100) NOT NULL,
    email           VARCHAR2(100) UNIQUE NOT NULL,
    phone           VARCHAR2(15),
    status          VARCHAR2(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at      DATE DEFAULT SYSDATE,
    role            VARCHAR2(20) DEFAULT 'CUSTOMER' CHECK (role IN ('ADMIN', 'CUSTOMER')), -- Added for admin users
    password_hash   VARCHAR2(100) -- Added for authentication
);

CREATE TABLE Gear (
    gear_id             NUMBER PRIMARY KEY,
    name                VARCHAR2(100) NOT NULL,
    category            VARCHAR2(50),
    brand               VARCHAR2(50),
    rent_price_per_day  NUMBER(8,2) CHECK (rent_price_per_day >= 0),
    sub_price_per_month NUMBER(8,2) CHECK (sub_price_per_month >= 0),
    stock               NUMBER DEFAULT 0 CHECK (stock >= 0),
    status              VARCHAR2(20) DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE', 'UNAVAILABLE')),
    CONSTRAINT uniq_gear_name UNIQUE (name)
);

CREATE TABLE Rentals (
    rent_id             NUMBER PRIMARY KEY,
    user_id             NUMBER REFERENCES Users(user_id) ON DELETE CASCADE,
    gear_id             NUMBER REFERENCES Gear(gear_id) ON DELETE CASCADE,
    start_date          DATE NOT NULL,
    end_date            DATE,
    return_date         DATE,
    status              VARCHAR2(20) DEFAULT 'RENTED' CHECK (status IN ('RENTED', 'RETURNED')),
    condition_returned  VARCHAR2(50) CHECK (condition_returned IN ('GOOD', 'DAMAGED', 'BROKEN')), -- Added for gear condition
    CONSTRAINT chk_dates CHECK (end_date >= start_date),
    CONSTRAINT uniq_rental_once UNIQUE (user_id, gear_id, start_date)
);

CREATE TABLE Subscriptions (
    sub_id      NUMBER PRIMARY KEY,
    user_id     NUMBER REFERENCES Users(user_id) ON DELETE CASCADE,
    gear_id     NUMBER REFERENCES Gear(gear_id) ON DELETE CASCADE,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    is_active   CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')),
    CONSTRAINT uniq_sub_once UNIQUE (user_id, gear_id, start_date)
);

CREATE TABLE Payments (
    payment_id  NUMBER PRIMARY KEY,
    user_id     NUMBER REFERENCES Users(user_id) ON DELETE CASCADE,
    amount      NUMBER(10,2) CHECK (amount >= 0),
    payment_date DATE DEFAULT SYSDATE,
    type        VARCHAR2(20) CHECK (type IN ('RENTAL', 'SUBSCRIPTION', 'PENALTY')),
    ref_id      NUMBER -- refers to rent_id, sub_id, or penalty_id based on type
);

CREATE TABLE Penalties (
    penalty_id  NUMBER PRIMARY KEY,
    rent_id     NUMBER REFERENCES Rentals(rent_id) ON DELETE CASCADE,
    amount      NUMBER(10,2) CHECK (amount >= 0),
    reason      VARCHAR2(255),
    status      VARCHAR2(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PAID'))
);

CREATE TABLE Audit_Log (
    log_id      NUMBER PRIMARY KEY,
    user_id     NUMBER REFERENCES Users(user_id),
    table_name  VARCHAR2(30),
    action      VARCHAR2(100),
    timestamp   DATE DEFAULT SYSDATE,
    details     VARCHAR2(4000)
);

-- INDEX FOR PERFORMANCE
CREATE INDEX idx_rentals_user_id ON Rentals(user_id);

-- SEQUENCES FOR AUTOINCREMENT
CREATE SEQUENCE users_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE gear_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE rentals_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE subs_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE payments_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE penalties_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE audit_seq START WITH 1 INCREMENT BY 1;

-- TRIGGERS FOR AUTOINCREMENT

CREATE OR REPLACE TRIGGER trg_users_bi
BEFORE INSERT ON Users
FOR EACH ROW
BEGIN
    :NEW.user_id := users_seq.NEXTVAL;
END;
/

CREATE OR REPLACE TRIGGER trg_gear_bi
BEFORE INSERT ON Gear
FOR EACH ROW
BEGIN
    :NEW.gear_id := gear_seq.NEXTVAL;
END;
/

CREATE OR REPLACE TRIGGER trg_rentals_bi
BEFORE INSERT ON Rentals
FOR EACH ROW
BEGIN
    :NEW.rent_id := rentals_seq.NEXTVAL;
END;
/

CREATE OR REPLACE TRIGGER trg_subs_bi
BEFORE INSERT ON Subscriptions
FOR EACH ROW
BEGIN
    :NEW.sub_id := subs_seq.NEXTVAL;
END;
/

CREATE OR REPLACE TRIGGER trg_payments_bi
BEFORE INSERT ON Payments
FOR EACH ROW
BEGIN
    :NEW.payment_id := payments_seq.NEXTVAL;
END;
/

CREATE OR REPLACE TRIGGER trg_penalties_bi
BEFORE INSERT ON Penalties
FOR EACH ROW
BEGIN
    :NEW.penalty_id := penalties_seq.NEXTVAL;
END;
/

CREATE OR REPLACE TRIGGER trg_audit_bi
BEFORE INSERT ON Audit_Log
FOR EACH ROW
BEGIN
    :NEW.log_id := audit_seq.NEXTVAL;
END;
/

-- PACKAGE FOR USER OPERATIONS
CREATE OR REPLACE PACKAGE pkg_user_ops AS
    PROCEDURE register_user(p_name IN VARCHAR2, p_email IN VARCHAR2, p_phone IN VARCHAR2, 
                          p_password IN VARCHAR2, p_role IN VARCHAR2 DEFAULT 'CUSTOMER');
    PROCEDURE deactivate_user(p_user_id IN NUMBER);
    FUNCTION get_user_info(p_user_id IN NUMBER) RETURN VARCHAR2;
    FUNCTION verify_user(p_email IN VARCHAR2, p_password IN VARCHAR2) RETURN NUMBER;
END pkg_user_ops;
/

CREATE OR REPLACE PACKAGE BODY pkg_user_ops AS
    PROCEDURE register_user(p_name IN VARCHAR2, p_email IN VARCHAR2, p_phone IN VARCHAR2, 
                          p_password IN VARCHAR2, p_role IN VARCHAR2 DEFAULT 'CUSTOMER') IS
    BEGIN
        IF p_name IS NULL OR p_email IS NULL THEN
            RAISE_APPLICATION_ERROR(-20014, 'Name and email are required');
        END IF;
        IF p_password IS NULL THEN
            RAISE_APPLICATION_ERROR(-20054, 'Password is required');
        END IF;
        IF p_role NOT IN ('ADMIN', 'CUSTOMER') THEN
            RAISE_APPLICATION_ERROR(-20055, 'Invalid role');
        END IF;
        INSERT INTO Users(name, email, phone, password_hash, role)
        VALUES (p_name, p_email, p_phone, p_password, p_role); -- Store plain password for simplicity; use DBMS_CRYPTO for production
    END register_user;

    PROCEDURE deactivate_user(p_user_id IN NUMBER) IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count FROM Users WHERE user_id = p_user_id;
        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20015, 'User does not exist');
        END IF;
        UPDATE Users SET status = 'INACTIVE' WHERE user_id = p_user_id;
    END deactivate_user;

    FUNCTION get_user_info(p_user_id IN NUMBER) RETURN VARCHAR2 IS
        v_info VARCHAR2(500);
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count FROM Users WHERE user_id = p_user_id;
        IF v_count = 0 THEN
            RETURN 'User not found';
        END IF;
        SELECT 'Name: ' || name || ', Email: ' || email || ', Phone: ' || NVL(phone, 'N/A') || 
               ', Status: ' || status || ', Role: ' || role || 
               ', Created: ' || TO_CHAR(created_at, 'YYYY-MM-DD')
        INTO v_info
        FROM Users
        WHERE user_id = p_user_id;
        RETURN v_info;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 'User not found';
    END get_user_info;

    FUNCTION verify_user(p_email IN VARCHAR2, p_password IN VARCHAR2) RETURN NUMBER IS
        v_user_id NUMBER;
        v_hash VARCHAR2(100);
    BEGIN
        SELECT user_id, password_hash INTO v_user_id, v_hash
        FROM Users
        WHERE email = p_email;
        IF v_hash = p_password THEN -- Replace with DBMS_CRYPTO comparison in production
            RETURN v_user_id;
        END IF;
        RETURN 0;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 0;
    END verify_user;
END pkg_user_ops;
/

-- PACKAGE FOR GEAR OPERATIONS
CREATE OR REPLACE PACKAGE pkg_gear_ops AS
    PROCEDURE add_gear(p_user_id IN NUMBER, p_name IN VARCHAR2, p_category IN VARCHAR2, p_brand IN VARCHAR2, 
                       p_rent_price_per_day IN NUMBER, p_sub_price_per_month IN NUMBER, 
                       p_stock IN NUMBER); 
    PROCEDURE update_stock(p_gear_id IN NUMBER, p_qty IN NUMBER); 
    FUNCTION is_gear_available(p_gear_id IN NUMBER) RETURN BOOLEAN;
END pkg_gear_ops;
/

CREATE OR REPLACE PACKAGE BODY pkg_gear_ops AS
    PROCEDURE add_gear(p_user_id IN NUMBER, p_name IN VARCHAR2, p_category IN VARCHAR2, p_brand IN VARCHAR2, 
                       p_rent_price_per_day IN NUMBER, p_sub_price_per_month IN NUMBER, 
                       p_stock IN NUMBER) IS
        v_role VARCHAR2(20);
    BEGIN
        SELECT role INTO v_role FROM Users WHERE user_id = p_user_id;
        IF v_role != 'ADMIN' THEN
            RAISE_APPLICATION_ERROR(-20052, 'Only admins can add gear');
        END IF;
        IF p_name IS NULL THEN
            RAISE_APPLICATION_ERROR(-20016, 'Gear name is required');
        END IF;
        IF p_rent_price_per_day < 0 OR p_sub_price_per_month < 0 OR p_stock < 0 THEN
            RAISE_APPLICATION_ERROR(-20017, 'Prices and stock cannot be negative');
        END IF;
        INSERT INTO Gear (name, category, brand, rent_price_per_day, sub_price_per_month, stock)
        VALUES (p_name, p_category, p_brand, p_rent_price_per_day, p_sub_price_per_month, p_stock);
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20015, 'User does not exist');
    END add_gear;
    
    PROCEDURE update_stock(p_gear_id IN NUMBER, p_qty IN NUMBER) IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count FROM Gear WHERE gear_id = p_gear_id;
        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20018, 'Gear does not exist');
        END IF;
        UPDATE Gear
        SET stock = stock + p_qty
        WHERE gear_id = p_gear_id;
        IF SQL%ROWCOUNT = 0 THEN
            RAISE_APPLICATION_ERROR(-20019, 'Stock update failed');
        END IF;
    END update_stock;
    
    FUNCTION is_gear_available(p_gear_id IN NUMBER) RETURN BOOLEAN IS
        v_stock NUMBER;
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count FROM Gear WHERE gear_id = p_gear_id;
        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20020, 'Gear does not exist');
        END IF;
        SELECT stock INTO v_stock
        FROM Gear
        WHERE gear_id = p_gear_id;        
        RETURN v_stock > 0;
    END is_gear_available;  
END pkg_gear_ops;
/

-- PACKAGE FOR RENTAL OPERATIONS
CREATE OR REPLACE PACKAGE pkg_rental_ops AS
    PROCEDURE rent_gear(p_user_id IN NUMBER, p_gear_id IN NUMBER, p_start IN DATE, p_end IN DATE);
    PROCEDURE return_gear(p_rent_id IN NUMBER, p_return_date IN DATE, p_condition IN VARCHAR2);
    FUNCTION calc_rental_charge(p_rent_id IN NUMBER) RETURN NUMBER;
END pkg_rental_ops;
/

CREATE OR REPLACE PACKAGE BODY pkg_rental_ops AS
    PROCEDURE rent_gear(p_user_id IN NUMBER, p_gear_id IN NUMBER, p_start IN DATE, p_end IN DATE) IS
        v_user_count NUMBER;
        v_gear_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_user_count FROM Users WHERE user_id = p_user_id;
        IF v_user_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20021, 'User does not exist');
        END IF;
        SELECT COUNT(*) INTO v_gear_count FROM Gear WHERE gear_id = p_gear_id;
        IF v_gear_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20022, 'Gear does not exist');
        END IF;
        IF NOT pkg_gear_ops.is_gear_available(p_gear_id) THEN
            RAISE_APPLICATION_ERROR(-20023, 'Gear not available for rent');
        END IF;
        INSERT INTO Rentals (user_id, gear_id, start_date, end_date)
        VALUES (p_user_id, p_gear_id, p_start, p_end);
        pkg_gear_ops.update_stock(p_gear_id, -1);
    END rent_gear;

    PROCEDURE return_gear(p_rent_id IN NUMBER, p_return_date IN DATE, p_condition IN VARCHAR2) IS
        v_count NUMBER;
        v_gear_id NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count FROM Rentals WHERE rent_id = p_rent_id;
        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20024, 'Rental does not exist');
        END IF;
        IF p_condition NOT IN ('GOOD', 'DAMAGED', 'BROKEN') THEN
            RAISE_APPLICATION_ERROR(-20056, 'Invalid condition; must be GOOD, DAMAGED, or BROKEN');
        END IF;
        UPDATE Rentals
        SET return_date = p_return_date, status = 'RETURNED', condition_returned = p_condition
        WHERE rent_id = p_rent_id;
        SELECT gear_id INTO v_gear_id
        FROM Rentals
        WHERE rent_id = p_rent_id;
        pkg_gear_ops.update_stock(v_gear_id, 1);
        IF p_condition IN ('DAMAGED', 'BROKEN') THEN
            pkg_penalty_center.assign_penalty(p_rent_id, 
                'Gear returned in ' || LOWER(p_condition) || ' condition');
        END IF;
    END return_gear;

    FUNCTION calc_rental_charge(p_rent_id IN NUMBER) RETURN NUMBER IS
        v_start_date DATE;
        v_end_date DATE;
        v_rent_price_per_day NUMBER;
        v_charge NUMBER;
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count FROM Rentals WHERE rent_id = p_rent_id;
        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20025, 'Rental does not exist');
        END IF;
        SELECT start_date, NVL(return_date, end_date), rent_price_per_day
        INTO v_start_date, v_end_date, v_rent_price_per_day
        FROM Rentals r
        JOIN Gear g ON r.gear_id = g.gear_id
        WHERE r.rent_id = p_rent_id;
        IF v_end_date IS NULL THEN
            v_end_date := SYSDATE;
        END IF;
        v_charge := CEIL(v_end_date - v_start_date) * v_rent_price_per_day;
        RETURN v_charge;
    END calc_rental_charge;
END pkg_rental_ops;
/

-- PACKAGE FOR SUBSCRIPTION SERVICE
CREATE OR REPLACE PACKAGE pkg_subscription_service AS
    PROCEDURE subscribe_gear(p_user_id IN NUMBER, p_gear_id IN NUMBER, p_start IN DATE, p_end IN DATE);
    PROCEDURE cancel_subscription(p_sub_id IN NUMBER);   
    FUNCTION is_active_sub(p_user_id IN NUMBER, p_gear_id IN NUMBER) RETURN BOOLEAN;
END pkg_subscription_service;
/

CREATE OR REPLACE PACKAGE BODY pkg_subscription_service AS
    PROCEDURE subscribe_gear(p_user_id IN NUMBER, p_gear_id IN NUMBER, p_start IN DATE, p_end IN DATE) IS
        v_user_count NUMBER;
        v_gear_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_user_count FROM Users WHERE user_id = p_user_id;
        IF v_user_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20026, 'User does not exist');
        END IF;
        SELECT COUNT(*) INTO v_gear_count FROM Gear WHERE gear_id = p_gear_id;
        IF v_gear_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20027, 'Gear does not exist');
        END IF;
        IF p_end < p_start THEN
            RAISE_APPLICATION_ERROR(-20028, 'End date cannot be before start date');
        END IF;
        IF is_active_sub(p_user_id, p_gear_id) THEN
            RAISE_APPLICATION_ERROR(-20029, 'User already has an active subscription for this gear');
        END IF;
        INSERT INTO Subscriptions (user_id, gear_id, start_date, end_date, is_active)
        VALUES (p_user_id, p_gear_id, p_start, p_end, 'Y');
    END subscribe_gear;

    PROCEDURE cancel_subscription(p_sub_id IN NUMBER) IS
        v_is_active CHAR(1);
    BEGIN
        BEGIN
            SELECT is_active INTO v_is_active 
            FROM Subscriptions 
            WHERE sub_id = p_sub_id;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20030, 'Subscription does not exist');
        END;  
        IF v_is_active = 'N' THEN
            RAISE_APPLICATION_ERROR(-20063, 'Subscription is already inactive');
        END IF;
        UPDATE Subscriptions
        SET is_active = 'N'
        WHERE sub_id = p_sub_id;
    END cancel_subscription;

    FUNCTION is_active_sub(p_user_id IN NUMBER, p_gear_id IN NUMBER) RETURN BOOLEAN IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count
        FROM Subscriptions
        WHERE user_id = p_user_id
          AND gear_id = p_gear_id
          AND is_active = 'Y'
          AND end_date >= SYSDATE;          
        RETURN v_count > 0;
    END is_active_sub;
END pkg_subscription_service;
/

CREATE OR REPLACE PACKAGE BODY pkg_payment_gateway AS
    PROCEDURE make_payment(p_user_id IN NUMBER, p_type IN VARCHAR2, p_ref_id IN NUMBER, p_amt IN NUMBER) IS
        v_count NUMBER;
        v_payment_exists NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count FROM Users WHERE user_id = p_user_id;
        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20031, 'User does not exist');
        END IF;
        IF p_amt < 0 THEN
            RAISE_APPLICATION_ERROR(-20032, 'Payment amount cannot be negative');
        END IF;
        IF p_type NOT IN ('RENTAL', 'SUBSCRIPTION', 'PENALTY') THEN
            RAISE_APPLICATION_ERROR(-20033, 'Invalid payment type; must be RENTAL, SUBSCRIPTION, or PENALTY');
        END IF;
        IF NOT validate_ref(p_type, p_ref_id) THEN
            RAISE_APPLICATION_ERROR(-20034, 'Invalid reference for the given payment type');
        END IF;
        SELECT COUNT(*) INTO v_payment_exists
        FROM Payments
        WHERE type = p_type AND ref_id = p_ref_id;
        IF v_payment_exists > 0 THEN
            RAISE_APPLICATION_ERROR(-20062, 'Payment already made for this reference');
        END IF;
        INSERT INTO Payments (user_id, amount, type, ref_id)
        VALUES (p_user_id, p_amt, p_type, p_ref_id);
    END make_payment;
    
    FUNCTION validate_ref(p_type IN VARCHAR2, p_ref_id IN NUMBER) RETURN BOOLEAN IS
        v_count INTEGER;
    BEGIN
        IF p_type = 'RENTAL' THEN
            SELECT COUNT(*) INTO v_count FROM Rentals WHERE rent_id = p_ref_id;
        ELSIF p_type = 'SUBSCRIPTION' THEN
            SELECT COUNT(*) INTO v_count FROM Subscriptions WHERE sub_id = p_ref_id;
        ELSIF p_type = 'PENALTY' THEN
            SELECT COUNT(*) INTO v_count FROM Penalties WHERE penalty_id = p_ref_id;
        ELSE
            RETURN FALSE;
        END IF;
        RETURN v_count > 0;
    END validate_ref;
END pkg_payment_gateway;
/

-- PACKAGE FOR PENALTIES
CREATE OR REPLACE PACKAGE pkg_penalty_center AS
    PROCEDURE assign_penalty(p_rent_id IN NUMBER, p_reason IN VARCHAR2);
    PROCEDURE resolve_penalty(p_penalty_id IN NUMBER);
    FUNCTION calc_penalty_amt(p_rent_id IN NUMBER) RETURN NUMBER;
END pkg_penalty_center;
/

CREATE OR REPLACE PACKAGE BODY pkg_penalty_center AS
    PROCEDURE assign_penalty(p_rent_id IN NUMBER, p_reason IN VARCHAR2) IS
        v_rent_status VARCHAR2(20);
        v_penalty_amt NUMBER(10, 2);
        v_count NUMBER;
        v_condition VARCHAR2(50);
    BEGIN
        SELECT COUNT(*) INTO v_count FROM Rentals WHERE rent_id = p_rent_id;
        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20034, 'Rental does not exist');
        END IF;
        SELECT status, condition_returned INTO v_rent_status, v_condition
        FROM Rentals
        WHERE rent_id = p_rent_id;
        IF v_rent_status = 'RENTED' OR v_condition IN ('DAMAGED', 'BROKEN') THEN
            v_penalty_amt := calc_penalty_amt(p_rent_id);
            IF v_penalty_amt > 0 OR v_condition IN ('DAMAGED', 'BROKEN') THEN
                INSERT INTO Penalties (rent_id, amount, reason)
                VALUES (p_rent_id, v_penalty_amt, p_reason);
            ELSE
                RAISE_APPLICATION_ERROR(-20035, 'No penalty applicable');
            END IF;
        ELSE
            RAISE_APPLICATION_ERROR(-20036, 'Rental is not overdue or has already been returned');
        END IF;
    END assign_penalty;

    PROCEDURE resolve_penalty(p_penalty_id IN NUMBER) IS
        v_status VARCHAR2(20);
    BEGIN
        BEGIN
            SELECT status INTO v_status 
            FROM Penalties 
            WHERE penalty_id = p_penalty_id;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                RAISE_APPLICATION_ERROR(-20037, 'Penalty does not exist');
        END;
        IF v_status = 'PAID' THEN
            RAISE_APPLICATION_ERROR(-20061, 'Penalty has already been resolved and paid');
        END IF;
        UPDATE Penalties
        SET status = 'PAID'
        WHERE penalty_id = p_penalty_id;
    END resolve_penalty;

    FUNCTION calc_penalty_amt(p_rent_id IN NUMBER) RETURN NUMBER IS
        v_rent_end_date DATE;
        v_return_date DATE;
        v_days_overdue NUMBER;
        v_rent_price_per_day NUMBER;
        v_penalty_amt NUMBER(10, 2) := 0;
        v_count NUMBER;
        v_condition VARCHAR2(50);
    BEGIN
        SELECT COUNT(*) INTO v_count FROM Rentals WHERE rent_id = p_rent_id;
        IF v_count = 0 THEN
            RAISE_APPLICATION_ERROR(-20038, 'Rental does not exist');
        END IF;
        SELECT r.end_date, NVL(r.return_date, SYSDATE), g.rent_price_per_day, r.condition_returned
        INTO v_rent_end_date, v_return_date, v_rent_price_per_day, v_condition
        FROM Rentals r
        JOIN Gear g ON r.gear_id = g.gear_id
        WHERE r.rent_id = p_rent_id;
        
        IF v_return_date > v_rent_end_date THEN
            v_days_overdue := CEIL(v_return_date - v_rent_end_date);          
            v_penalty_amt := v_days_overdue * (v_rent_price_per_day * 2); -- 2x daily rate per overdue day
        END IF;
        IF v_condition = 'DAMAGED' THEN
            v_penalty_amt := v_penalty_amt + 100; -- Additional $100 for damaged gear
        ELSIF v_condition = 'BROKEN' THEN
            v_penalty_amt := v_penalty_amt + 200; -- Additional $200 for broken gear
        END IF;
        RETURN v_penalty_amt;
    END calc_penalty_amt;
END pkg_penalty_center;
/

-- PACKAGE FOR AUDITS
CREATE OR REPLACE PACKAGE pkg_audit_trail AS
    PROCEDURE log_action(p_user_id IN NUMBER, p_table_name IN VARCHAR2, p_action IN VARCHAR2, p_details IN VARCHAR2);
    PROCEDURE get_audit_log(p_table_name IN VARCHAR2, p_start_date IN DATE, p_end_date IN DATE, p_cursor OUT SYS_REFCURSOR);
END pkg_audit_trail;
/

CREATE OR REPLACE PACKAGE BODY pkg_audit_trail AS
    PROCEDURE log_action(p_user_id IN NUMBER, p_table_name IN VARCHAR2, p_action IN VARCHAR2, p_details IN VARCHAR2) IS
    BEGIN
        INSERT INTO Audit_Log (user_id, table_name, action, details)
        VALUES (p_user_id, p_table_name, p_action, p_details);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE_APPLICATION_ERROR(-20050, 'Audit log insertion failed: ' || SQLERRM);
    END log_action;

    PROCEDURE get_audit_log(p_table_name IN VARCHAR2, p_start_date IN DATE, p_end_date IN DATE, p_cursor OUT SYS_REFCURSOR) IS
    BEGIN
        OPEN p_cursor FOR
        SELECT log_id, user_id, table_name, action, timestamp, details
        FROM Audit_Log
        WHERE table_name = NVL(p_table_name, table_name)
          AND timestamp BETWEEN p_start_date AND p_end_date
        ORDER BY timestamp DESC;
    END get_audit_log;
END pkg_audit_trail;
/

-- RENTAL LIMIT TRIGGER
CREATE OR REPLACE TRIGGER trg_rental_limit
BEFORE INSERT ON Rentals
FOR EACH ROW
DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM Rentals
    WHERE user_id = :NEW.user_id AND status = 'RENTED';
    IF v_count >= 3 THEN
        RAISE_APPLICATION_ERROR(-20053, 'User has reached rental limit of 3 active rentals');
    END IF;
END;
/

-- AUDIT TRIGGERS FOR ALL CHANGES

CREATE OR REPLACE TRIGGER trg_users_audit
AFTER INSERT OR UPDATE OR DELETE ON Users
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        pkg_audit_trail.log_action(:NEW.user_id, 'Users', 'INSERT', 
            'User added: ID=' || :NEW.user_id || ', Name=' || :NEW.name || 
            ', Email=' || :NEW.email || ', Phone=' || NVL(:NEW.phone, 'NULL') || 
            ', Status=' || :NEW.status || ', Role=' || :NEW.role || 
            ', Created_at=' || TO_CHAR(:NEW.created_at, 'YYYY-MM-DD'));
    ELSIF UPDATING THEN
        IF :OLD.name != :NEW.name THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Users', 'UPDATE', 
                'User name changed from ' || :OLD.name || ' to ' || :NEW.name);
        END IF;
        IF :OLD.email != :NEW.email THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Users', 'UPDATE', 
                'User email changed from ' || :OLD.email || ' to ' || :NEW.email);
        END IF;
        IF NVL(:OLD.phone, 'NULL') != NVL(:NEW.phone, 'NULL') THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Users', 'UPDATE', 
                'User phone changed from ' || NVL(:OLD.phone, 'NULL') || ' to ' || NVL(:NEW.phone, 'NULL'));
        END IF;
        IF :OLD.status != :NEW.status THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Users', 'UPDATE', 
                'User status changed from ' || :OLD.status || ' to ' || :NEW.status);
        END IF;
        IF :OLD.role != :NEW.role THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Users', 'UPDATE', 
                'User role changed from ' || :OLD.role || ' to ' || :NEW.role);
        END IF;
        IF NVL(:OLD.password_hash, 'NULL') != NVL(:NEW.password_hash, 'NULL') THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Users', 'UPDATE', 
                'User password_hash changed');
        END IF;
        IF :OLD.created_at != :NEW.created_at THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Users', 'UPDATE', 
                'User created_at changed from ' || TO_CHAR(:OLD.created_at, 'YYYY-MM-DD') || 
                ' to ' || TO_CHAR(:NEW.created_at, 'YYYY-MM-DD'));
        END IF;
    ELSIF DELETING THEN
        pkg_audit_trail.log_action(:OLD.user_id, 'Users', 'DELETE', 
            'User deleted: ID=' || :OLD.user_id || ', Name=' || :OLD.name || 
            ', Email=' || :OLD.email || ', Phone=' || NVL(:OLD.phone, 'NULL') || 
            ', Status=' || :OLD.status || ', Role=' || :OLD.role || 
            ', Created_at=' || TO_CHAR(:OLD.created_at, 'YYYY-MM-DD'));
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_gear_audit
AFTER INSERT OR UPDATE OR DELETE ON Gear
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        pkg_audit_trail.log_action(NULL, 'Gear', 'INSERT', 
            'Gear added: ID=' || :NEW.gear_id || ', Name=' || :NEW.name || 
            ', Category=' || NVL(:NEW.category, 'NULL') || ', Brand=' || NVL(:NEW.brand, 'NULL') || 
            ', Rent_price=' || :NEW.rent_price_per_day || ', Sub_price=' || :NEW.sub_price_per_month || 
            ', Stock=' || :NEW.stock || ', Status=' || :NEW.status);
    ELSIF UPDATING THEN
        IF :OLD.name != :NEW.name THEN
            pkg_audit_trail.log_action(NULL, 'Gear', 'UPDATE', 
                'Gear name changed from ' || :OLD.name || ' to ' || :NEW.name);
        END IF;
        IF NVL(:OLD.category, 'NULL') != NVL(:NEW.category, 'NULL') THEN
            pkg_audit_trail.log_action(NULL, 'Gear', 'UPDATE', 
                'Gear category changed from ' || NVL(:OLD.category, 'NULL') || ' to ' || NVL(:NEW.category, 'NULL'));
        END IF;
        IF NVL(:OLD.brand, 'NULL') != NVL(:NEW.brand, 'NULL') THEN
            pkg_audit_trail.log_action(NULL, 'Gear', 'UPDATE', 
                'Gear brand changed from ' || NVL(:OLD.brand, 'NULL') || ' to ' || NVL(:NEW.brand, 'NULL'));
        END IF;
        IF :OLD.rent_price_per_day != :NEW.rent_price_per_day THEN
            pkg_audit_trail.log_action(NULL, 'Gear', 'UPDATE', 
                'Gear rent_price_per_day changed from ' || :OLD.rent_price_per_day || ' to ' || :NEW.rent_price_per_day);
        END IF;
        IF :OLD.sub_price_per_month != :NEW.sub_price_per_month THEN
            pkg_audit_trail.log_action(NULL, 'Gear', 'UPDATE', 
                'Gear sub_price_per_month changed from ' || :OLD.sub_price_per_month || ' to ' || :NEW.sub_price_per_month);
        END IF;
        IF :OLD.stock != :NEW.stock THEN
            pkg_audit_trail.log_action(NULL, 'Gear', 'UPDATE', 
                'Gear stock changed from ' || :OLD.stock || ' to ' || :NEW.stock);
        END IF;
        IF :OLD.status != :NEW.status THEN
            pkg_audit_trail.log_action(NULL, 'Gear', 'UPDATE', 
                'Gear status changed from ' || :OLD.status || ' to ' || :NEW.status);
        END IF;
    ELSIF DELETING THEN
        pkg_audit_trail.log_action(NULL, 'Gear', 'DELETE', 
            'Gear deleted: ID=' || :OLD.gear_id || ', Name=' || :OLD.name || 
            ', Category=' || NVL(:OLD.category, 'NULL') || ', Brand=' || NVL(:OLD.brand, 'NULL') || 
            ', Rent_price=' || :OLD.rent_price_per_day || ', Sub_price=' || :OLD.sub_price_per_month || 
            ', Stock=' || :OLD.stock || ', Status=' || :OLD.status);
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_rentals_audit
AFTER INSERT OR UPDATE OR DELETE ON Rentals
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        pkg_audit_trail.log_action(:NEW.user_id, 'Rentals', 'INSERT', 
            'Rental added: ID=' || :NEW.rent_id || ', User=' || :NEW.user_id || 
            ', Gear=' || :NEW.gear_id || ', Start_date=' || TO_CHAR(:NEW.start_date, 'YYYY-MM-DD') || 
            ', End_date=' || NVL(TO_CHAR(:NEW.end_date, 'YYYY-MM-DD'), 'NULL') || 
            ', Return_date=' || NVL(TO_CHAR(:NEW.return_date, 'YYYY-MM-DD'), 'NULL') || 
            ', Status=' || :NEW.status || ', Condition=' || NVL(:NEW.condition_returned, 'NULL'));
    ELSIF UPDATING THEN
        IF :OLD.user_id != :NEW.user_id THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Rentals', 'UPDATE', 
                'Rental user_id changed from ' || :OLD.user_id || ' to ' || :NEW.user_id);
        END IF;
        IF :OLD.gear_id != :NEW.gear_id THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Rentals', 'UPDATE', 
                'Rental gear_id changed from ' || :OLD.gear_id || ' to ' || :NEW.gear_id);
        END IF;
        IF :OLD.start_date != :NEW.start_date THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Rentals', 'UPDATE', 
                'Rental start_date changed from ' || TO_CHAR(:OLD.start_date, 'YYYY-MM-DD') || 
                ' to ' || TO_CHAR(:NEW.start_date, 'YYYY-MM-DD'));
        END IF;
        IF NVL(TO_CHAR(:OLD.end_date, 'YYYY-MM-DD'), 'NULL') != NVL(TO_CHAR(:NEW.end_date, 'YYYY-MM-DD'), 'NULL') THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Rentals', 'UPDATE', 
                'Rental end_date changed from ' || NVL(TO_CHAR(:OLD.end_date, 'YYYY-MM-DD'), 'NULL') || 
                ' to ' || NVL(TO_CHAR(:NEW.end_date, 'YYYY-MM-DD'), 'NULL'));
        END IF;
        IF NVL(TO_CHAR(:OLD.return_date, 'YYYY-MM-DD'), 'NULL') != NVL(TO_CHAR(:NEW.return_date, 'YYYY-MM-DD'), 'NULL') THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Rentals', 'UPDATE', 
                'Rental return_date changed from ' || NVL(TO_CHAR(:OLD.return_date, 'YYYY-MM-DD'), 'NULL') || 
                ' to ' || NVL(TO_CHAR(:NEW.return_date, 'YYYY-MM-DD'), 'NULL'));
        END IF;
        IF :OLD.status != :NEW.status THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Rentals', 'UPDATE', 
                'Rental status changed from ' || :OLD.status || ' to ' || :NEW.status);
        END IF;
        IF NVL(:OLD.condition_returned, 'NULL') != NVL(:NEW.condition_returned, 'NULL') THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Rentals', 'UPDATE', 
                'Rental condition_returned changed from ' || NVL(:OLD.condition_returned, 'NULL') || 
                ' to ' || NVL(:NEW.condition_returned, 'NULL'));
        END IF;
    ELSIF DELETING THEN
        pkg_audit_trail.log_action(:OLD.user_id, 'Rentals', 'DELETE', 
            'Rental deleted: ID=' || :OLD.rent_id || ', User=' || :OLD.user_id || 
            ', Gear=' || :OLD.gear_id || ', Start_date=' || TO_CHAR(:OLD.start_date, 'YYYY-MM-DD') || 
            ', End_date=' || NVL(TO_CHAR(:OLD.end_date, 'YYYY-MM-DD'), 'NULL') || 
            ', Return_date=' || NVL(TO_CHAR(:OLD.return_date, 'YYYY-MM-DD'), 'NULL') || 
            ', Status=' || :OLD.status || ', Condition=' || NVL(:OLD.condition_returned, 'NULL'));
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_subscriptions_audit
AFTER INSERT OR UPDATE OR DELETE ON Subscriptions
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        pkg_audit_trail.log_action(:NEW.user_id, 'Subscriptions', 'INSERT', 
            'Subscription added: ID=' || :NEW.sub_id || ', User=' || :NEW.user_id || 
            ', Gear=' || :NEW.gear_id || ', Start_date=' || TO_CHAR(:NEW.start_date, 'YYYY-MM-DD') || 
            ', End_date=' || TO_CHAR(:NEW.end_date, 'YYYY-MM-DD') || ', Is_active=' || :NEW.is_active);
    ELSIF UPDATING THEN
        IF :OLD.user_id != :NEW.user_id THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Subscriptions', 'UPDATE', 
                'Subscription user_id changed from ' || :OLD.user_id || ' to ' || :NEW.user_id);
        END IF;
        IF :OLD.gear_id != :NEW.gear_id THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Subscriptions', 'UPDATE', 
                'Subscription gear_id changed from ' || :OLD.gear_id || ' to ' || :NEW.gear_id);
        END IF;
        IF :OLD.start_date != :NEW.start_date THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Subscriptions', 'UPDATE', 
                'Subscription start_date changed from ' || TO_CHAR(:OLD.start_date, 'YYYY-MM-DD') || 
                ' to ' || TO_CHAR(:NEW.start_date, 'YYYY-MM-DD'));
        END IF;
        IF :OLD.end_date != :NEW.end_date THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Subscriptions', 'UPDATE', 
                'Subscription end_date changed from ' || TO_CHAR(:OLD.end_date, 'YYYY-MM-DD') || 
                ' to ' || TO_CHAR(:NEW.end_date, 'YYYY-MM-DD'));
        END IF;
        IF :OLD.is_active != :NEW.is_active THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Subscriptions', 'UPDATE', 
                'Subscription is_active changed from ' || :OLD.is_active || ' to ' || :NEW.is_active);
        END IF;
    ELSIF DELETING THEN
        pkg_audit_trail.log_action(:OLD.user_id, 'Subscriptions', 'DELETE', 
            'Subscription deleted: ID=' || :OLD.sub_id || ', User=' || :OLD.user_id || 
            ', Gear=' || :OLD.gear_id || ', Start_date=' || TO_CHAR(:OLD.start_date, 'YYYY-MM-DD') || 
            ', End_date=' || TO_CHAR(:OLD.end_date, 'YYYY-MM-DD') || ', Is_active=' || :OLD.is_active);
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_payments_audit
AFTER INSERT OR UPDATE OR DELETE ON Payments
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        pkg_audit_trail.log_action(:NEW.user_id, 'Payments', 'INSERT', 
            'Payment added: ID=' || :NEW.payment_id || ', User=' || :NEW.user_id || 
            ', Amount=' || :NEW.amount || ', Payment_date=' || TO_CHAR(:NEW.payment_date, 'YYYY-MM-DD') || 
            ', Type=' || :NEW.type || ', Ref_id=' || :NEW.ref_id);
    ELSIF UPDATING THEN
        IF :OLD.user_id != :NEW.user_id THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Payments', 'UPDATE', 
                'Payment user_id changed from ' || :OLD.user_id || ' to ' || :NEW.user_id);
        END IF;
        IF :OLD.amount != :NEW.amount THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Payments', 'UPDATE', 
                'Payment amount changed from ' || :OLD.amount || ' to ' || :NEW.amount);
        END IF;
        IF :OLD.payment_date != :NEW.payment_date THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Payments', 'UPDATE', 
                'Payment payment_date changed from ' || TO_CHAR(:OLD.payment_date, 'YYYY-MM-DD') || 
                ' to ' || TO_CHAR(:NEW.payment_date, 'YYYY-MM-DD'));
        END IF;
        IF :OLD.type != :NEW.type THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Payments', 'UPDATE', 
                'Payment type changed from ' || :OLD.type || ' to ' || :NEW.type);
        END IF;
        IF :OLD.ref_id != :NEW.ref_id THEN
            pkg_audit_trail.log_action(:NEW.user_id, 'Payments', 'UPDATE', 
                'Payment ref_id changed from ' || :OLD.ref_id || ' to ' || :NEW.ref_id);
        END IF;
    ELSIF DELETING THEN
        pkg_audit_trail.log_action(:OLD.user_id, 'Payments', 'DELETE', 
            'Payment deleted: ID=' || :OLD.payment_id || ', User=' || :OLD.user_id || 
            ', Amount=' || :OLD.amount || ', Payment_date=' || TO_CHAR(:OLD.payment_date, 'YYYY-MM-DD') || 
            ', Type=' || :OLD.type || ', Ref_id=' || :OLD.ref_id);
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_penalties_audit
AFTER INSERT OR UPDATE OR DELETE ON Penalties
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        pkg_audit_trail.log_action(NULL, 'Penalties', 'INSERT', 
            'Penalty added: ID=' || :NEW.penalty_id || ', Rent_id=' || :NEW.rent_id || 
            ', Amount=' || :NEW.amount || ', Reason=' || NVL(:NEW.reason, 'NULL') || 
            ', Status=' || :NEW.status);
    ELSIF UPDATING THEN
        IF :OLD.rent_id != :NEW.rent_id THEN
            pkg_audit_trail.log_action(NULL, 'Penalties', 'UPDATE', 
                'Penalty rent_id changed from ' || :OLD.rent_id || ' to ' || :NEW.rent_id);
        END IF;
        IF :OLD.amount != :NEW.amount THEN
            pkg_audit_trail.log_action(NULL, 'Penalties', 'UPDATE', 
                'Penalty amount changed from ' || :OLD.amount || ' to ' || :NEW.amount);
        END IF;
        IF NVL(:OLD.reason, 'NULL') != NVL(:NEW.reason, 'NULL') THEN
            pkg_audit_trail.log_action(NULL, 'Penalties', 'UPDATE', 
                'Penalty reason changed from ' || NVL(:OLD.reason, 'NULL') || ' to ' || NVL(:NEW.reason, 'NULL'));
        END IF;
        IF :OLD.status != :NEW.status THEN
            pkg_audit_trail.log_action(NULL, 'Penalties', 'UPDATE', 
                'Penalty status changed from ' || :OLD.status || ' to ' || :NEW.status);
        END IF;
    ELSIF DELETING THEN
        pkg_audit_trail.log_action(NULL, 'Penalties', 'DELETE', 
            'Penalty deleted: ID=' || :OLD.penalty_id || ', Rent_id=' || :OLD.rent_id || 
            ', Amount=' || :OLD.amount || ', Reason=' || NVL(:OLD.reason, 'NULL') || 
            ', Status=' || :OLD.status);
    END IF;
END;
/

-- SUBSCRIPTION EXPIRY TRIGGER
CREATE OR REPLACE TRIGGER trg_subscriptions_expiry
BEFORE UPDATE ON Subscriptions
FOR EACH ROW
BEGIN
    IF :NEW.end_date < SYSDATE AND :NEW.is_active = 'Y' THEN
        :NEW.is_active := 'N';
    END IF;
END;
/

-- PAYMENT REFERENCE VALIDATION TRIGGER
CREATE OR REPLACE TRIGGER trg_check_payment_ref
BEFORE INSERT OR UPDATE ON Payments
FOR EACH ROW
BEGIN
    IF NOT pkg_payment_gateway.validate_ref(:NEW.type, :NEW.ref_id) THEN
        RAISE_APPLICATION_ERROR(-20010, 'Invalid reference for given payment type');
    END IF;
END;
/

-- VIEWS FOR FRONTEND
CREATE OR REPLACE VIEW v_available_gear AS
SELECT gear_id, name, category, brand, rent_price_per_day, sub_price_per_month, stock
FROM Gear
WHERE status = 'AVAILABLE' AND stock > 0;

CREATE OR REPLACE VIEW v_user_rentals AS
SELECT r.rent_id, u.user_id, u.name AS user_name, g.name AS gear_name, 
       r.start_date, r.end_date, r.return_date, r.status, r.condition_returned
FROM Rentals r
JOIN Users u ON r.user_id = u.user_id
JOIN Gear g ON r.gear_id = g.gear_id;

CREATE OR REPLACE VIEW v_user_subscriptions AS
SELECT s.sub_id, u.user_id, u.name AS user_name, g.name AS gear_name, 
       s.start_date, s.end_date, s.is_active
FROM Subscriptions s
JOIN Users u ON s.user_id = u.user_id
JOIN Gear g ON s.gear_id = g.gear_id;

select * from gear;
select * from users;
select * from rentals;
select * from penalties;
select * from subscriptions;
select * from audit_log;
select * from payments;
