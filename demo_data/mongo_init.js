// demo_data/mongo_init.js
db = db.getSiblingDB('analytics_demo');

// User profiles with nested structures
db.user_profiles.insertMany([
    {
        user_id: "user_001",
        name: "Alice Johnson",
        email: "alice@example.com",
        signup_date: new Date("2024-01-15"),
        profile: {
            age: 32,
            occupation: "Data Analyst",
            company: {
                name: "TechCorp",
                industry: "Technology",
                size: "500-1000"
            }
        },
        preferences: {
            theme: "dark",
            notifications: {
                email: true,
                push: false,
                sms: true
            },
            language: "en",
            dashboard_layout: ["revenue", "users", "conversion"]
        },
        subscription: {
            plan: "pro",
            status: "active",
            start_date: new Date("2024-01-15"),
            billing_cycle: "monthly",
            features: ["advanced_analytics", "api_access", "white_label"]
        },
        metadata: {
            tags: ["power_user", "beta_tester"],
            last_login: new Date("2024-01-25T10:30:00Z"),
            login_count: 45
        }
    },
    {
        user_id: "user_002",
        name: "Bob Smith",
        email: "bob@example.com",
        signup_date: new Date("2024-01-16"),
        profile: {
            age: 28,
            occupation: "Marketing Manager",
            company: {
                name: "MarketPro",
                industry: "Marketing",
                size: "50-100"
            }
        },
        preferences: {
            theme: "light",
            notifications: {
                email: false,
                push: true,
                sms: false
            },
            language: "en",
            dashboard_layout: ["campaigns", "roi", "traffic"]
        },
        subscription: {
            plan: "basic",
            status: "active",
            start_date: new Date("2024-01-16"),
            billing_cycle: "annual",
            features: ["basic_analytics"]
        },
        metadata: {
            tags: ["trial_converted"],
            last_login: new Date("2024-01-24T15:20:00Z"),
            login_count: 23
        }
    }
]);

// Complex events with nested properties and arrays
db.user_events.insertMany([
    {
        user_id: "user_001",
        event_type: "dashboard_interaction",
        timestamp: new Date("2024-01-20T09:15:00Z"),
        session_id: "sess_abc123",
        properties: {
            dashboard: {
                id: "dash_001",
                name: "Sales Analytics",
                widgets: [
                    {
                        type: "chart",
                        title: "Revenue Trend",
                        data_points: 120,
                        filters_applied: ["region:US", "period:monthly"]
                    },
                    {
                        type: "table",
                        title: "Top Products",
                        rows: 50,
                        columns: ["product", "revenue", "units"]
                    }
                ]
            },
            interactions: [
                { action: "filter_changed", field: "region", value: "US" },
                { action: "zoom", range: { start: "2024-01-01", end: "2024-01-20" } }
            ],
            performance: {
                load_time_ms: 234,
                query_time_ms: 89,
                render_time_ms: 145
            }
        }
    },
    {
        user_id: "user_001",
        event_type: "query_executed",
        timestamp: new Date("2024-01-20T09:20:00Z"),
        session_id: "sess_abc123",
        properties: {
            query: {
                type: "sql",
                database: "sales_db",
                tables: ["orders", "customers", "products"],
                joins: 2,
                filters: {
                    date_range: { start: "2024-01-01", end: "2024-01-20" },
                    conditions: ["status = 'completed'", "amount > 100"]
                },
                aggregations: ["SUM", "AVG", "COUNT"]
            },
            results: {
                rows_returned: 1543,
                execution_time_ms: 234,
                cached: false
            },
            errors: []
        }
    },
    {
        user_id: "user_002",
        event_type: "collaboration",
        timestamp: new Date("2024-01-21T11:00:00Z"),
        session_id: "sess_xyz789",
        properties: {
            action: "share_dashboard",
            dashboard_id: "dash_002",
            shared_with: [
                {
                    email: "colleague1@example.com",
                    role: "editor",
                    permissions: ["view", "edit", "comment"]
                },
                {
                    email: "colleague2@example.com",
                    role: "viewer",
                    permissions: ["view", "comment"]
                }
            ],
            settings: {
                expiry_date: new Date("2024-02-21"),
                password_protected: true,
                allow_download: false
            }
        }
    }
]);

// Product analytics with nested metrics
db.product_analytics.insertMany([
    {
        date: new Date("2024-01-20"),
        overall_metrics: {
            users: {
                daily_active: 45,
                weekly_active: 178,
                monthly_active: 523
            },
            engagement: {
                avg_session_duration_min: 24.5,
                sessions_per_user: 2.3,
                bounce_rate: 0.15
            }
        },
        feature_usage: {
            dashboards: {
                created: 12,
                viewed: 156,
                shared: 23,
                exported: 8
            },
            queries: {
                executed: 234,
                saved: 45,
                failed: 3
            },
            data_sources: {
                connected: 8,
                active: 6,
                types: {
                    postgresql: 3,
                    mysql: 2,
                    mongodb: 3
                }
            }
        },
        revenue: {
            mrr: 12500.00,
            new_customers: 8,
            churned_customers: 2,
            expansion_revenue: 1200.00,
            contraction_revenue: 300.00
        },
        geographic_distribution: [
            { country: "US", users: 25, revenue: 7500.00 },
            { country: "UK", users: 10, revenue: 3000.00 },
            { country: "DE", users: 6, revenue: 1500.00 },
            { country: "FR", users: 4, revenue: 500.00 }
        ]
    }
]);

// System logs with complex nested data
db.system_logs.insertMany([
    {
        timestamp: new Date("2024-01-20T10:30:00Z"),
        level: "error",
        service: "query_engine",
        message: "Database connection pool exhausted",
        context: {
            pool: {
                max_connections: 20,
                active_connections: 20,
                queued_requests: 15
            },
            database: {
                host: "db.example.com",
                port: 5432,
                name: "production"
            },
            affected_users: ["user_003", "user_007"],
            retry_attempts: 3
        },
        stack_trace: [
            "at QueryEngine.execute (query.js:123)",
            "at DatabasePool.getConnection (pool.js:45)",
            "at Connection.timeout (connection.js:89)"
        ],
        resolved: true,
        resolution_time_sec: 120
    }
]);

// Customer orders with embedded line items
db.orders.insertMany([
    {
        order_id: "ORD-001",
        customer: {
            id: "user_001",
            name: "Alice Johnson",
            email: "alice@example.com",
            shipping_address: {
                street: "123 Main St",
                city: "New York",
                state: "NY",
                zip: "10001",
                country: "US",
                coordinates: { lat: 40.7128, lng: -74.0060 }
            }
        },
        items: [
            {
                product_id: "PROD-A",
                name: "Pro Dashboard License",
                quantity: 5,
                unit_price: 99.00,
                discount: 10.00,
                tax: 44.50,
                subtotal: 445.00,
                metadata: {
                    category: "software",
                    subscription_months: 12
                }
            },
            {
                product_id: "PROD-B",
                name: "API Access",
                quantity: 1,
                unit_price: 199.00,
                discount: 0,
                tax: 19.90,
                subtotal: 199.00,
                metadata: {
                    category: "addon",
                    rate_limit: 10000
                }
            }
        ],
        payment: {
            method: "credit_card",
            status: "completed",
            transaction_id: "TXN-12345",
            processor: "stripe",
            amount: 708.40,
            currency: "USD",
            processed_at: new Date("2024-01-20T09:30:00Z")
        },
        fulfillment: {
            status: "delivered",
            tracking_number: "TRACK-001",
            carrier: "digital",
            delivered_at: new Date("2024-01-20T09:35:00Z")
        },
        order_date: new Date("2024-01-20T09:25:00Z"),
        notes: ["Customer requested invoice", "Applied enterprise discount"]
    }
]);

// Create indexes
db.user_events.createIndex({ "user_id": 1, "timestamp": -1 });
db.user_events.createIndex({ "properties.dashboard.id": 1 });
db.orders.createIndex({ "customer.id": 1 });
db.orders.createIndex({ "order_date": -1 });
db.product_analytics.createIndex({ "date": -1 });

print("✅ Complex MongoDB demo database initialized!");
print("Collections: " + db.getCollectionNames().length);