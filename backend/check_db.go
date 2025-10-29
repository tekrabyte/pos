package main

import (
        "database/sql"
        "fmt"
        "log"
        "os"

        _ "github.com/go-sql-driver/mysql"
        "github.com/joho/godotenv"
)

func main() {
        // Load env
        godotenv.Load()

        dbHost := os.Getenv("DB_HOST")
        dbPort := os.Getenv("DB_PORT")
        dbUser := os.Getenv("DB_USER")
        dbPassword := os.Getenv("DB_PASSWORD")
        dbName := os.Getenv("DB_NAME")

        dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4",
                dbUser, dbPassword, dbHost, dbPort, dbName)

        db, err := sql.Open("mysql", dsn)
        if err != nil {
                log.Fatal(err)
        }
        defer db.Close()

        // Show tables
        fmt.Println("=== TABLES IN DATABASE ===")
        rows, err := db.Query("SHOW TABLES")
        if err != nil {
                log.Fatal(err)
        }
        defer rows.Close()

        var tables []string
        for rows.Next() {
                var table string
                rows.Scan(&table)
                tables = append(tables, table)
                fmt.Println(table)
        }

        fmt.Println("\n=== CHECKING EXISTING TABLES ===")
        
        // Check each table structure
        for _, table := range tables {
                fmt.Printf("\n--- %s ---\n", table)
                colRows, err := db.Query("DESCRIBE " + table)
                if err != nil {
                        continue
                }
                
                for colRows.Next() {
                        var field, colType, null, key, defaultVal, extra sql.NullString
                        colRows.Scan(&field, &colType, &null, &key, &defaultVal, &extra)
                        fmt.Printf("  %s (%s)\n", field.String, colType.String)
                }
                colRows.Close()
        }
}
