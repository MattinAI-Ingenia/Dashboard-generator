// demo_data/mongo_init.js
// Initialize demo MongoDB database with sample data

// Switch to the analytics demo database
db = db.getSiblingDB('analytics_demo');

// Create collections and insert sample data

// User profiles collection
db.user_profiles.insertMany([
    {
        user_id: "user_001",
        name: "Alice Johnson",
        email: "alice@example.com",
        signup_date: new Date("2024-01-15"),
        preferences: {
            theme: "dark",
            notifications: true,
            language: "en"
        }
    },
    {
        user_id: "user_002",
        name: "Bob Smith",
        email: "bob@example.com",
        signup_date: new Date("2024-01-16"),
        preferences: {
            theme: "light",
            notifications: false,
            language: "en"
        }
    },
    {
        user_id: "user_003",
        name: "Carol Davis",
        email: "carol@example.com",
        signup_date: new Date("2024-01-17"),
        preferences: {
            theme: "dark",
            notifications: true,
            language: "es"
        }
    },
    {
        user_id: "user_004",
        name: "David Wilson",
        email: "david@example.com",
        signup_date: new Date("2024-01-18"),
        preferences: {
            theme: "light",
            notifications: true,
            language: "en"
        }
    },
    {
        user_id: "user_005",
        name: "Eva Brown",
        email: "eva@example.com",
        signup_date: new Date("2024-01-19"),
        preferences: {
            theme: "auto",
            notifications: false,
            language: "fr"
        }
    }
]);

// User events collection with more comprehensive data
db.user_events.insertMany([
    // User 001 events
    {
        user_id: "user_001",
        event_type: "login",
        timestamp: new Date("2024-01-20T09:00:00Z"),
        properties: {
            device: "desktop",
            browser: "chrome",
            location: "New York",
            ip: "192.168.1.100"
        }
    },
    {
        user_id: "user_001",
        event_type: "page_view",
        timestamp: new Date("2024-01-20T09:05:00Z"),
        properties: {
            page: "/dashboard",
            duration: 120,
            referrer: "/login"
        }
    },
    {
        user_id: "user_001",
        event_type: "dashboard_created",
        timestamp: new Date("2024-01-20T09:15:00Z"),
        properties: {
            dashboard_name: "Sales Analytics",
            template: "sales"
        }
    },
    {
        user_id: "user_001",
        event_type: "visualization_added",
        timestamp: new Date("2024-01-20T09:20:00Z"),
        properties: {
            dashboard_id: "dash_001",
            viz_type: "bar_chart",
            data_source: "sales_db"
        }
    },
    {
        user_id: "user_001",
        event_type: "logout",
        timestamp: new Date("2024-01-20T11:30:00Z"),
        properties: {
            session_duration: 9000
        }
    },
    
    // User 002 events
    {
        user_id: "user_002",
        event_type: "login",
        timestamp: new Date("2024-01-20T10:00:00Z"),
        properties: {
            device: "mobile",
            browser: "safari",
            location: "San Francisco",
            ip: "192.168.1.101"
        }
    },
    {
        user_id: "user_002",
        event_type: "page_view",
        timestamp: new Date("2024-01-20T10:02:00Z"),
        properties: {
            page: "/dashboards",
            duration: 45,
            referrer: "/home"
        }
    },
    {
        user_id: "user_002",
        event_type: "click",
        timestamp: new Date("2024-01-20T10:03:00Z"),
        properties: {
            element: "create_dashboard",
            page: "/dashboards"
        }
    },
    {
        user_id: "user_002",
        event_type: "data_source_connected",
        timestamp: new Date("2024-01-20T10:10:00Z"),
        properties: {
            source_type: "postgresql",
            source_name: "Production DB"
        }
    },
    
    // User 003 events (signup flow)
    {
        user_id: "user_003",
        event_type: "signup",
        timestamp: new Date("2024-01-17T14:30:00Z"),
        properties: {
            source: "google_ads",
            campaign: "dashboard_2024",
            device: "desktop"
        }
    },
    {
        user_id: "user_003",
        event_type: "email_verified",
        timestamp: new Date("2024-01-17T14:35:00Z"),
        properties: {
            verification_time: 300
        }
    },
    {
        user_id: "user_003",
        event_type: "onboarding_started",
        timestamp: new Date("2024-01-17T14:40:00Z"),
        properties: {
            step: "welcome"
        }
    },
    {
        user_id: "user_003",
        event_type: "onboarding_completed",
        timestamp: new Date("2024-01-17T15:00:00Z"),
        properties: {
            steps_completed: 5,
            total_time: 1200
        }
    },
    
    // User 004 events
    {
        user_id: "user_004",
        event_type: "login",
        timestamp: new Date("2024-01-21T08:30:00Z"),
        properties: {
            device: "tablet",
            browser: "firefox",
            location: "Chicago"
        }
    },
    {
        user_id: "user_004",
        event_type: "search",
        timestamp: new Date("2024-01-21T08:35:00Z"),
        properties: {
            query: "sales by region",
            results_count: 15
        }
    },
    {
        user_id: "user_004",
        event_type: "export_dashboard",
        timestamp: new Date("2024-01-21T09:00:00Z"),
        properties: {
            dashboard_id: "dash_004",
            format: "pdf",
            file_size: 2048000
        }
    },
    
    // User 005 events
    {
        user_id: "user_005",
        event_type: "login",
        timestamp: new Date("2024-01-22T16:45:00Z"),
        properties: {
            device: "desktop",
            browser: "edge",
            location: "London"
        }
    },
    {
        user_id: "user_005",
        event_type: "collaboration_invite",
        timestamp: new Date("2024-01-22T17:00:00Z"),
        properties: {
            dashboard_id: "dash_005",
            invited_email: "colleague@example.com",
            permission_level: "viewer"
        }
    }
]);

// Product analytics collection
db.product_analytics.insertMany([
    {
        date: new Date("2024-01-20"),
        metrics: {
            daily_active_users: 45,
            new_signups: 8,
            dashboards_created: 12,
            queries_executed: 156,
            data_sources_connected: 3
        }
    },
    {
        date: new Date("2024-01-21"),
        metrics: {
            daily_active_users: 52,
            new_signups: 6,
            dashboards_created: 15,
            queries_executed: 203,
            data_sources_connected: 5
        }
    },
    {
        date: new Date("2024-01-22"),
        metrics: {
            daily_active_users: 48,
            new_signups: 4,
            dashboards_created: 9,
            queries_executed: 187,
            data_sources_connected: 2
        }
    }
]);

// Error logs collection
db.error_logs.insertMany([
    {
        timestamp: new Date("2024-01-20T10:30:00Z"),
        user_id: "user_002",
        error_type: "connection_timeout",
        message: "Database connection timeout",
        stack_trace: "ConnectionError: timeout after 30s",
        resolved: true
    },
    {
        timestamp: new Date("2024-01-21T14:15:00Z"),
        user_id: "user_004",
        error_type: "query_error",
        message: "Invalid SQL syntax",
        stack_trace: "SyntaxError: unexpected token at line 1",
        resolved: false
    }
]);

// Create indexes for better query performance
db.user_events.createIndex({ "user_id": 1, "timestamp": -1 });
db.user_events.createIndex({ "event_type": 1 });
db.user_events.createIndex({ "timestamp": -1 });

db.user_profiles.createIndex({ "user_id": 1 });
db.user_profiles.createIndex({ "email": 1 });

db.product_analytics.createIndex({ "date": -1 });

db.error_logs.createIndex({ "timestamp": -1 });
db.error_logs.createIndex({ "resolved": 1 });

// Create a user with read/write permissions
db.createUser({
    user: "demo_user",
    pwd: "demo_pass",
    roles: [
        {
            role: "readWrite",
            db: "analytics_demo"
        }
    ]
});

print("MongoDB demo database initialized successfully!");
print("Collections created:");
print("- user_profiles (" + db.user_profiles.countDocuments() + " documents)");
print("- user_events (" + db.user_events.countDocuments() + " documents)");
print("- product_analytics (" + db.product_analytics.countDocuments() + " documents)");
print("- error_logs (" + db.error_logs.countDocuments() + " documents)");