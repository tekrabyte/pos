package main

import (
	"database/sql"
	"fmt"
	"os"
	"time"

	_ "github.com/go-sql-driver/mysql"
)

var DB *sql.DB

func InitDatabase() error {
	dbHost := os.Getenv("DB_HOST")
	dbPort := os.Getenv("DB_PORT")
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")

	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4",
		dbUser, dbPassword, dbHost, dbPort, dbName)

	var err error
	DB, err = sql.Open("mysql", dsn)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}

	// Set connection pool settings
	DB.SetMaxOpenConns(25)
	DB.SetMaxIdleConns(5)
	DB.SetConnMaxLifetime(5 * time.Minute)

	// Test connection
	if err := DB.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	return nil
}

func CloseDatabase() {
	if DB != nil {
		DB.Close()
	}
}

// RunMigrations runs database migrations
func RunMigrations() error {
	migrations := []string{
		// Add is_bundle column
		`ALTER TABLE products ADD COLUMN is_bundle BOOLEAN DEFAULT FALSE AFTER status`,
		
		// Add bundle_items column (JSON/TEXT)
		`ALTER TABLE products ADD COLUMN bundle_items TEXT DEFAULT NULL AFTER is_bundle`,
		
		// Add has_portions column
		`ALTER TABLE products ADD COLUMN has_portions BOOLEAN DEFAULT FALSE AFTER bundle_items`,
		
		// Add unit column
		`ALTER TABLE products ADD COLUMN unit VARCHAR(50) DEFAULT 'pcs' AFTER has_portions`,
		
		// Add portion_size column
		`ALTER TABLE products ADD COLUMN portion_size DECIMAL(10,2) DEFAULT 1.00 AFTER unit`,
	}

	fmt.Println("🚀 Running database migrations...")
	
	for i, migration := range migrations {
		if _, err := DB.Exec(migration); err != nil {
			// Check if error is because column already exists
			if !isDuplicateColumnError(err) {
				fmt.Printf("⚠️  Migration %d failed: %v\n", i+1, err)
			} else {
				fmt.Printf("✓ Migration %d: Column already exists (skipped)\n", i+1)
			}
		} else {
			fmt.Printf("✅ Migration %d completed\n", i+1)
		}
	}

	// Update existing products with default values
	updateQuery := `
		UPDATE products 
		SET is_bundle = COALESCE(is_bundle, FALSE), 
		    has_portions = COALESCE(has_portions, FALSE), 
		    unit = COALESCE(unit, 'pcs'), 
		    portion_size = COALESCE(portion_size, 1.00)
		WHERE unit IS NULL OR portion_size IS NULL OR is_bundle IS NULL OR has_portions IS NULL
	`
	
	fmt.Println("📝 Updating existing products with defaults...")
	result, err := DB.Exec(updateQuery)
	if err != nil {
		fmt.Printf("⚠️  Update failed: %v\n", err)
	} else {
		rows, _ := result.RowsAffected()
		fmt.Printf("✅ %d products updated\n", rows)
	}

	fmt.Println("🎉 Migrations completed!")
	return nil
}

// Helper function to check if error is duplicate column
func isDuplicateColumnError(err error) bool {
	if err == nil {
		return false
	}
	return fmt.Sprintf("%v", err) == "Error 1060: Duplicate column name 'is_bundle'" ||
	       fmt.Sprintf("%v", err) == "Error 1060: Duplicate column name 'bundle_items'" ||
	       fmt.Sprintf("%v", err) == "Error 1060: Duplicate column name 'has_portions'" ||
	       fmt.Sprintf("%v", err) == "Error 1060: Duplicate column name 'unit'" ||
	       fmt.Sprintf("%v", err) == "Error 1060: Duplicate column name 'portion_size'"
}
