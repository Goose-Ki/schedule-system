package models

import (
	"time"
)

type User struct {
	ID         uint      `gorm:"primaryKey" json:"id"`
	TelegramID int64     `gorm:"uniqueIndex;not null" json:"telegram_id"`
	Username   string    `json:"username"`
	FirstName  string    `json:"first_name"`
	CreatedAt  time.Time `json:"created_at"`
}

type ScheduleItem struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	UserID      uint      `gorm:"not null" json:"user_id"`
	DayOfWeek   string    `gorm:"not null" json:"day_of_week"`
	TimeStart   string    `gorm:"not null" json:"time_start"`
	TimeEnd     string    `gorm:"not null" json:"time_end"`
	Subject     string    `gorm:"not null" json:"subject"`
	Description string    `json:"description"`
	CreatedAt   time.Time `json:"created_at"`

	User User `gorm:"foreignKey:UserID" json:"-"`
}
