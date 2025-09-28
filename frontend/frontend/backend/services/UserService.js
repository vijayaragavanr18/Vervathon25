const { v4: uuidv4 } = require('uuid');

class UserService {
  constructor(databaseService) {
    this.db = databaseService;
  }

  async createUser(username, email) {
    try {
      // Validate input
      if (!username || !email) {
        throw new Error('Username and email are required');
      }

      // Validate email format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        throw new Error('Invalid email format');
      }

      // Check if user already exists
      const existingUser = await this.findUserByEmail(email);
      if (existingUser) {
        throw new Error('User with this email already exists');
      }

      // Create user ID
      const userId = uuidv4();

      // Create user in database
      const user = await this.db.createUser(userId, username, email);
      
      console.log(`👤 Created new user: ${username} (${email})`);
      
      // Award welcome bonus
      await this.awardWelcomeBonus(userId);
      
      return user;
      
    } catch (error) {
      console.error('❌ Error creating user:', error);
      throw error;
    }
  }

  async getUser(userId) {
    try {
      const user = await this.db.getUser(userId);
      return this.formatUser(user);
    } catch (error) {
      console.error('❌ Error getting user:', error);
      throw error;
    }
  }

  async findUserByEmail(email) {
    try {
      const user = await this.db.get('SELECT * FROM users WHERE email = ?', [email]);
      return user ? this.formatUser(user) : null;
    } catch (error) {
      console.error('❌ Error finding user by email:', error);
      return null;
    }
  }

  async findUserByUsername(username) {
    try {
      const user = await this.db.get('SELECT * FROM users WHERE username = ?', [username]);
      return user ? this.formatUser(user) : null;
    } catch (error) {
      console.error('❌ Error finding user by username:', error);
      return null;
    }
  }

  async updateUser(userId, updates) {
    try {
      const allowedFields = ['username', 'email'];
      const updateFields = [];
      const updateValues = [];

      for (const [field, value] of Object.entries(updates)) {
        if (allowedFields.includes(field) && value !== undefined) {
          updateFields.push(`${field} = ?`);
          updateValues.push(value);
        }
      }

      if (updateFields.length === 0) {
        throw new Error('No valid fields to update');
      }

      updateValues.push(userId);
      
      await this.db.run(
        `UPDATE users SET ${updateFields.join(', ')}, updated_at = CURRENT_TIMESTAMP WHERE id = ?`,
        updateValues
      );

      return await this.getUser(userId);
      
    } catch (error) {
      console.error('❌ Error updating user:', error);
      throw error;
    }
  }

  async deleteUser(userId) {
    try {
      // In a real application, you might want to soft delete or archive user data
      // For now, we'll just mark as deleted (you'd need to add a deleted field to the schema)
      
      console.log(`🗑️  User deletion requested for: ${userId}`);
      
      // Instead of actually deleting, we could:
      // 1. Anonymize the user data
      // 2. Mark as deleted with a timestamp
      // 3. Remove personal information but keep analytics data
      
      throw new Error('User deletion not implemented - contact administrator');
      
    } catch (error) {
      console.error('❌ Error deleting user:', error);
      throw error;
    }
  }

  async getUserProgress(userId) {
    try {
      const user = await this.getUser(userId);
      const stats = await this.db.getUserStats(userId);
      
      // Calculate progress metrics
      const progress = {
        user: {
          id: user.id,
          username: user.username,
          level: user.level,
          xp: user.xp,
          joinedAt: user.created_at
        },
        stats: {
          documents: stats.documents,
          chat: stats.chat,
          quiz: stats.quiz,
          achievements: stats.achievements
        },
        level: {
          current: user.level,
          xp: user.xp,
          xpToNextLevel: this.calculateXPToNextLevel(user.xp),
          progress: this.calculateLevelProgress(user.xp)
        },
        badges: await this.getUserBadges(userId),
        streak: await this.getUserStreak(userId)
      };
      
      return progress;
      
    } catch (error) {
      console.error('❌ Error getting user progress:', error);
      throw error;
    }
  }

  calculateXPToNextLevel(currentXP) {
    const currentLevel = Math.floor(currentXP / 100) + 1;
    const nextLevelXP = currentLevel * 100;
    return nextLevelXP - currentXP;
  }

  calculateLevelProgress(currentXP) {
    const currentLevel = Math.floor(currentXP / 100) + 1;
    const levelBaseXP = (currentLevel - 1) * 100;
    const levelXP = currentXP - levelBaseXP;
    return (levelXP / 100) * 100; // Percentage
  }

  async getUserBadges(userId) {
    try {
      // Get user's achievements and convert them to badges
      const achievements = await this.db.getUserAchievements(userId);
      
      const badges = achievements.map(achievement => ({
        id: achievement.id,
        type: achievement.achievement_type,
        title: achievement.title,
        description: achievement.description,
        earnedAt: achievement.unlocked_at,
        xpReward: achievement.xp_reward
      }));
      
      // Add level-based badges
      const user = await this.getUser(userId);
      if (user.level >= 5) {
        badges.push({
          id: 'level_5',
          type: 'level_milestone',
          title: 'Learning Enthusiast',
          description: 'Reached level 5',
          earnedAt: user.updated_at,
          xpReward: 0
        });
      }
      
      if (user.level >= 10) {
        badges.push({
          id: 'level_10',
          type: 'level_milestone',
          title: 'Knowledge Seeker',
          description: 'Reached level 10',
          earnedAt: user.updated_at,
          xpReward: 0
        });
      }
      
      return badges;
      
    } catch (error) {
      console.error('❌ Error getting user badges:', error);
      return [];
    }
  }

  async getUserStreak(userId) {
    try {
      // Calculate user's learning streak based on activity
      const transactions = await this.db.getUserXPTransactions(userId);
      
      if (transactions.length === 0) {
        return { current: 0, longest: 0 };
      }
      
      // Group transactions by date
      const activityByDate = {};
      
      transactions.forEach(transaction => {
        const date = new Date(transaction.created_at).toDateString();
        if (!activityByDate[date]) {
          activityByDate[date] = true;
        }
      });
      
      const activeDates = Object.keys(activityByDate).sort((a, b) => new Date(a) - new Date(b));
      
      // Calculate current streak
      let currentStreak = 0;
      const today = new Date().toDateString();
      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toDateString();
      
      // Check if user was active today or yesterday
      if (activeDates.includes(today) || activeDates.includes(yesterday)) {
        let checkDate = new Date();
        
        // Count backwards from today
        while (activeDates.includes(checkDate.toDateString())) {
          currentStreak++;
          checkDate = new Date(checkDate.getTime() - 24 * 60 * 60 * 1000);
        }
      }
      
      // Calculate longest streak
      let longestStreak = 0;
      let tempStreak = 0;
      let previousDate = null;
      
      for (const dateString of activeDates) {
        const currentDate = new Date(dateString);
        
        if (previousDate) {
          const dayDiff = (currentDate - previousDate) / (24 * 60 * 60 * 1000);
          
          if (dayDiff === 1) {
            tempStreak++;
          } else {
            longestStreak = Math.max(longestStreak, tempStreak);
            tempStreak = 1;
          }
        } else {
          tempStreak = 1;
        }
        
        previousDate = currentDate;
      }
      
      longestStreak = Math.max(longestStreak, tempStreak);
      
      return {
        current: currentStreak,
        longest: longestStreak,
        lastActivity: activeDates[activeDates.length - 1]
      };
      
    } catch (error) {
      console.error('❌ Error calculating user streak:', error);
      return { current: 0, longest: 0 };
    }
  }

  async awardWelcomeBonus(userId) {
    try {
      // Award welcome XP
      await this.db.updateUserXP(userId, 50);
      await this.db.addXPTransaction(userId, 'welcome_bonus', 50, 'Welcome to the AI Educational Avatar!');
      
      // Award welcome achievement
      await this.db.addAchievement(
        userId,
        'first_login',
        'Welcome Aboard!',
        'Started your learning journey with the AI Educational Avatar',
        25
      );
      
      console.log(`🎉 Welcome bonus awarded to user: ${userId}`);
      
    } catch (error) {
      console.error('❌ Error awarding welcome bonus:', error);
    }
  }

  async recordUserActivity(userId, activityType, details = null) {
    try {
      // Record activity in XP transactions for streak calculation
      const xpRewards = {
        'login': 5,
        'document_view': 2,
        'chat_message': 1,
        'quiz_attempt': 10,
        'study_session': 15
      };
      
      const xpAmount = xpRewards[activityType] || 1;
      
      await this.db.addXPTransaction(
        userId,
        activityType,
        xpAmount,
        details || `${activityType} activity`
      );
      
      // Update user XP
      await this.db.updateUserXP(userId, xpAmount);
      
    } catch (error) {
      console.error('❌ Error recording user activity:', error);
    }
  }

  formatUser(user) {
    if (!user) return null;
    
    return {
      id: user.id,
      username: user.username,
      email: user.email,
      xp: user.xp || 0,
      level: user.level || 1,
      created_at: user.created_at,
      updated_at: user.updated_at
    };
  }

  async getUserLeaderboard(limit = 10) {
    try {
      const topUsers = await this.db.all(
        'SELECT id, username, xp, level FROM users ORDER BY xp DESC LIMIT ?',
        [limit]
      );
      
      return topUsers.map((user, index) => ({
        rank: index + 1,
        id: user.id,
        username: user.username,
        xp: user.xp,
        level: user.level
      }));
      
    } catch (error) {
      console.error('❌ Error getting leaderboard:', error);
      return [];
    }
  }

  async searchUsers(query, limit = 10) {
    try {
      const users = await this.db.all(
        'SELECT id, username, email, xp, level FROM users WHERE username LIKE ? OR email LIKE ? LIMIT ?',
        [`%${query}%`, `%${query}%`, limit]
      );
      
      return users.map(user => this.formatUser(user));
      
    } catch (error) {
      console.error('❌ Error searching users:', error);
      return [];
    }
  }

  async validateUsername(username) {
    // Username validation rules
    const rules = {
      minLength: 3,
      maxLength: 30,
      allowedChars: /^[a-zA-Z0-9_-]+$/
    };
    
    if (!username || username.length < rules.minLength) {
      throw new Error(`Username must be at least ${rules.minLength} characters long`);
    }
    
    if (username.length > rules.maxLength) {
      throw new Error(`Username cannot exceed ${rules.maxLength} characters`);
    }
    
    if (!rules.allowedChars.test(username)) {
      throw new Error('Username can only contain letters, numbers, underscores, and hyphens');
    }
    
    // Check if username is taken
    const existingUser = await this.findUserByUsername(username);
    if (existingUser) {
      throw new Error('Username is already taken');
    }
    
    return true;
  }

  async validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!email || !emailRegex.test(email)) {
      throw new Error('Invalid email format');
    }
    
    // Check if email is taken
    const existingUser = await this.findUserByEmail(email);
    if (existingUser) {
      throw new Error('Email is already registered');
    }
    
    return true;
  }

  // Get user preferences (could be extended to store user settings)
  async getUserPreferences(userId) {
    try {
      // For now, return default preferences
      // In a real app, you'd have a preferences table
      return {
        language: 'en',
        notifications: true,
        theme: 'light',
        autoplay: true,
        difficulty: 'medium'
      };
    } catch (error) {
      console.error('❌ Error getting user preferences:', error);
      return {};
    }
  }

  async updateUserPreferences(userId, preferences) {
    try {
      // For now, just validate user exists
      await this.getUser(userId);
      
      // In a real app, you'd update the preferences table
      console.log(`📋 User preferences update requested for ${userId}:`, preferences);
      
      return preferences;
    } catch (error) {
      console.error('❌ Error updating user preferences:', error);
      throw error;
    }
  }
}

module.exports = UserService;