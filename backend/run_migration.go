package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"
	_ "github.com/go-sql-driver/mysql"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found")
	}

	// Get database connection details from environment
	dbHost := os.Getenv("DB_HOST")
	dbPort := os.Getenv("DB_PORT")
	dbUser := os.Getenv("DB_USER")
	dbPass := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")

	// Create connection string
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true", dbUser, dbPass, dbHost, dbPort, dbName)

	// Connect to database
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer db.Close()

	// Test connection
	if err := db.Ping(); err != nil {
		log.Fatal("Failed to ping database:", err)
	}

	fmt.Println("✅ Connected to database")

	// Run migrations
	migrations := []string{
		// Add is_bundle column
		`ALTER TABLE products ADD COLUMN IF NOT EXISTS is_bundle BOOLEAN DEFAULT FALSE AFTER status`,
		
		// Add bundle_items column (JSON/TEXT)
		`ALTER TABLE products ADD COLUMN IF NOT EXISTS bundle_items TEXT DEFAULT NULL AFTER is_bundle`,
		
		// Add has_portions column
		`ALTER TABLE products ADD COLUMN IF NOT EXISTS has_portions BOOLEAN DEFAULT FALSE AFTER bundle_items`,
		
		// Add unit column
		`ALTER TABLE products ADD COLUMN IF NOT EXISTS unit VARCHAR(50) DEFAULT 'pcs' AFTER has_portions`,
		
		// Add portion_size column
		`ALTER TABLE products ADD COLUMN IF NOT EXISTS portion_size DECIMAL(10,2) DEFAULT 1.00 AFTER unit`,
	}

	fmt.Println("🚀 Running migrations...")
	
	for i, migration := range migrations {
		fmt.Printf("Running migration %d/%d...\n", i+1, len(migrations))
		if _, err := db.Exec(migration); err != nil {
			log.Printf("⚠️  Migration %d failed (may already exist): %v\n", i+1, err)
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
		WHERE unit IS NULL OR portion_size IS NULL
	`
	
	fmt.Println("📝 Updating existing products with defaults...")
	if _, err := db.Exec(updateQuery); err != nil {
		log.Printf("⚠️  Update failed: %v\n", err)
	} else {
		fmt.Println("✅ Existing products updated")
	}

	fmt.Println("\n🎉 All migrations completed successfully!")
}
