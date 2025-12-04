package main

import (
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"schedule-backend/internal/database"
	"schedule-backend/internal/handlers"
)

var db *gorm.DB

func main() {
	// Инициализация базы данных
	db = database.InitDB()

	r := gin.Default()

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":   "OK",
			"service":  "schedule-backend",
			"database": "connected",
		})
	})

	// API routes
	api := r.Group("/api")
	{
		// User routes
		api.POST("/users", handlers.CreateUser(db))
		api.GET("/users/:telegram_id", handlers.GetUser(db))

		// Schedule routes
		api.POST("/schedule", handlers.CreateScheduleItem(db))
		api.GET("/schedule", handlers.GetSchedule(db))
		api.PUT("/schedule/:id", handlers.UpdateScheduleItem(db))
		api.DELETE("/schedule/:id", handlers.DeleteScheduleItem(db))
	}

	log.Println("🚀 Server starting on :8080")
	log.Println("📊 Health check: curl http://localhost:8080/health")
	log.Println("👤 Create user: curl -X POST http://localhost:8080/api/users -H 'Content-Type: application/json' -d '{\"telegram_id\":123456789,\"username\":\"test_user\"}'")

	r.Run(":8080")
}
