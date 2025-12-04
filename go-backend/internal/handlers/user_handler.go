package handlers

import (
	"strconv"

	"schedule-backend/internal/models"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

func CreateUser(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var user models.User
		if err := c.ShouldBindJSON(&user); err != nil {
			c.JSON(400, gin.H{"error": err.Error()})
			return
		}

		// Проверяем, существует ли пользователь
		var existingUser models.User
		result := db.Where("telegram_id = ?", user.TelegramID).First(&existingUser)

		if result.Error == nil {
			// Пользователь уже существует
			c.JSON(200, gin.H{"user": existingUser, "message": "User already exists"})
			return
		}

		// Создаем нового пользователя
		if err := db.Create(&user).Error; err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}

		c.JSON(201, gin.H{"user": user, "message": "User created successfully"})
	}
}

func GetUser(db *gorm.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		telegramID, err := strconv.ParseInt(c.Param("telegram_id"), 10, 64)
		if err != nil {
			c.JSON(400, gin.H{"error": "Invalid telegram ID"})
			return
		}

		var user models.User
		if err := db.Where("telegram_id = ?", telegramID).First(&user).Error; err != nil {
			c.JSON(404, gin.H{"error": "User not found"})
			return
		}

		c.JSON(200, gin.H{"user": user})
	}
}
