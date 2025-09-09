-- Users Table (for authentication and roles)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- Hashed password
    role ENUM('admin', 'merchandiser', 'builder') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,  -- Admin can disable (set to FALSE)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- States Table (e.g., Nigerian states for admin setup)
CREATE TABLE states (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL  -- e.g., 'Lagos', 'Abuja'
);

CREATE TABLE banks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL  -- e.g., 'Access Bank', 'GT Bank'
);

-- Locations Table (neighborhoods/markets within states)
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    state_id INTEGER REFERENCES states(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,  -- e.g., 'Ikeja', 'Yaba Market'
    UNIQUE(state_id, name)
);

-- SKUs Table (Stock Keeping Units for products, with category)
CREATE TABLE skus (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,  -- e.g., 'Seasoning'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    expiry_tracking BOOLEAN DEFAULT FALSE  -- Flag if expiry needs tracking
);

-- POSMs Table (Point of Sale Materials, setup by admin)
CREATE TABLE posms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL  -- e.g., 'Display Stand'
);

-- Outlets Table (Retail stores onboarded)
CREATE TABLE outlets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location_id INTEGER REFERENCES locations(id),
    classification ENUM('Neighborhood', 'Open_market','Wholesales','Retail') NOT NULL,
    outlet_type ENUM('Wholesaler', 'GSM-Groceries', 'Lock-Up Shop','Kiosks','Table Tops') NOT NULL,
    onboarded_by_user_id INTEGER REFERENCES users(id),
    onboarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gps_lat DECIMAL(10, 8),  -- GPS from onboarding
    gps_long DECIMAL(11, 8),
    outlet_image_key VARCHAR(255)  -- DO Spaces key for image
);

-- POSM Deployments Table (For builders)
CREATE TABLE posm_deployments (
    id SERIAL PRIMARY KEY,
    outlet_id INTEGER REFERENCES outlets(id),
    deployed_by_user_id INTEGER REFERENCES users(id),
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployed_posms JSONB,  -- e.g., [1, 3] (POSM IDs)
    before_image_key VARCHAR(255),  -- DO Spaces key
    after_image_key VARCHAR(255),   -- DO Spaces key
    gps_lat DECIMAL(10, 8),
    gps_long DECIMAL(11, 8)
);

-- MSL/SOS Tracks (Shelf facings, auto MSL)
CREATE TABLE msl_sos_tracks (
    id SERIAL PRIMARY KEY,
    outlet_id INTEGER REFERENCES outlets(id),
    tracked_by_user_id INTEGER REFERENCES users(id),
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sos_data JSONB,  -- e.g., {"1": 5, "2": 0} (sku_id: facings)
    msl_count INTEGER,  -- Computed: number of SKUs with facings > 0
    shelf_image_key VARCHAR(255),
    gps_lat DECIMAL(10, 8),
    gps_long DECIMAL(11, 8)
);

-- OOS Tracks
CREATE TABLE oos_tracks (
    id SERIAL PRIMARY KEY,
    outlet_id INTEGER REFERENCES outlets(id),
    tracked_by_user_id INTEGER REFERENCES users(id),
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    oos_data JSONB,  -- e.g., [{"sku_id":1, "reason":"low demand"}]
    gps_lat DECIMAL(10, 8),
    gps_long DECIMAL(11, 8)
);

-- Order Tracks
CREATE TABLE order_tracks (
    id SERIAL PRIMARY KEY,
    outlet_id INTEGER REFERENCES outlets(id),
    tracked_by_user_id INTEGER REFERENCES users(id),
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    order_data JSONB,  -- e.g., [{"sku_id":1, "quantity":10}]
    gps_lat DECIMAL(10, 8),
    gps_long DECIMAL(11, 8)
);

-- Expiry Tracks
CREATE TABLE expiry_tracks (
    id SERIAL PRIMARY KEY,
    outlet_id INTEGER REFERENCES outlets(id),
    tracked_by_user_id INTEGER REFERENCES users(id),
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_data JSONB,  -- e.g., [{"sku_id":1, "expiry_date":"2025-12-01"}]
    gps_lat DECIMAL(10, 8),
    gps_long DECIMAL(11, 8)
);

-- Indexes for performance
CREATE INDEX idx_outlets_location ON outlets(location_id);
CREATE INDEX idx_posm_deployments_outlet ON posm_deployments(outlet_id);
CREATE INDEX idx_msl_sos_outlet ON msl_sos_tracks(outlet_id);
CREATE INDEX idx_oos_outlet ON oos_tracks(outlet_id);
CREATE INDEX idx_order_outlet ON order_tracks(outlet_id);
CREATE INDEX idx_expiry_outlet ON expiry_tracks(outlet_id);