package main

import (
	"database/sql"
	"fmt"
	"log"
	
	_ "github.com/go-sql-driver/mysql"
)

func main() {
	dsn := "u215947863_pos_dev:Pos_dev123#@tcp(srv1412.hstgr.io:3306)/u215947863_pos_dev?parseTime=true&charset=utf8mb4"
	
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatalf("Failed to open database: %v", err)
	}
	defer db.Close()
	
	tables := []string{"products", "categories", "brands", "orders"}
	
	for _, table := range tables {
		fmt.Printf("\n=== Table: %s ===\n", table)
		rows, err := db.Query(fmt.Sprintf("DESCRIBE %s", table))
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			continue
		}
		
		fmt.Println("Columns:")
		for rows.Next() {
			var field, typ, null, key, defaultVal, extra sql.NullString
			rows.Scan(&field, &typ, &null, &key, &defaultVal, &extra)
			fmt.Printf("  - %s (%s)\n", field.String, typ.String)
		}
		rows.Close()
		
		// Count records
		var count int
		db.QueryRow(fmt.Sprintf("SELECT COUNT(*) FROM %s", table)).Scan(&count)
		fmt.Printf("Records: %d\n", count)
	}
}
