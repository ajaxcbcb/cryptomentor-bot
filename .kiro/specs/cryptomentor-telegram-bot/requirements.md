# Requirements Document: CryptoMentor Telegram Bot

## 1. Introduction

This document specifies the functional and non-functional requirements for the CryptoMentor Telegram Bot, a standalone Node.js application that provides users with an interactive interface to the Automaton AI trading system via Telegram.

## 2. Functional Requirements

### 2.1 Bot Initialization

**REQ-2.1.1**: The system SHALL initialize a Telegram bot instance using a valid bot token from environment variables.

**REQ-2.1.2**: The system SHALL establish polling connection with Telegram Bot API on startup.

**REQ-2.1.3**: The system SHALL register all command handlers (/start, /status, /help, /talk) during initialization.

**REQ-2.1.4**: The system SHALL configure error handlers for polling errors and general bot errors.

**REQ-2.1.5**: The system SHALL log successful initialization with timestamp and bot username.

### 2.2 User Registration and Greeting

**REQ-2.2.1**: The system SHALL respond to /start command by registering the user with the Automaton API.

**REQ-2.2.2**: The system SHALL send a welcome message containing the user's initial credit balance.

**REQ-2.2.3**: The system SHALL handle duplicate /start commands idempotently (no duplicate user accounts).

**REQ-2.2.4**: The system SHALL extract user information (Telegram ID, username, first name) from the message object.

**REQ-2.2.5**: The system SHALL provide a fallback welcome message if the Automaton API is unavailable.

### 2.3 Scheduled Notifications

**REQ-2.3.1**: The system SHALL send automated notifications to all active users at 08:00 WIB (UTC+7).

**REQ-2.3.2**: The system SHALL send automated notifications to all active users at 14:00 WIB (UTC+7).

**REQ-2.3.3**: The system SHALL send automated notifications to all active users at 20:00 WIB (UTC+7).

**REQ-2.3.4**: The system SHALL fetch notification content from the Automaton API before each scheduled delivery.

**REQ-2.3.5**: The system SHALL continue notification delivery to remaining users even if delivery to some users fails.

**REQ-2.3.6**: The system SHALL log delivery statistics (success count, failure count) after each notification batch.

**REQ-2.3.7**: The system SHALL use Asia/Jakarta timezone for all scheduled notifications.

### 2.4 Real-Time Conversation

**REQ-2.4.1**: The system SHALL respond to /talk command followed by user message text.

**REQ-2.4.2**: The system SHALL check user credit balance before processing conversation requests.

**REQ-2.4.3**: The system SHALL send "typing" chat action indicator while processing conversation requests.

**REQ-2.4.4**: The system SHALL forward user messages to the Automaton API chat endpoint.

**REQ-2.4.5**: The system SHALL deliver AI-generated responses from the API to the user.

**REQ-2.4.6**: The system SHALL notify users when they have insufficient credits for conversation.

**REQ-2.4.7**: The system SHALL handle API timeouts gracefully with user-friendly error messages.

### 2.5 Status Command

**REQ-2.5.1**: The system SHALL respond to /status command with user's current credit balance.

**REQ-2.5.2**: The system SHALL display user's conversation count in status response.

**REQ-2.5.3**: The system SHALL display user's last activity timestamp in status response.

**REQ-2.5.4**: The system SHALL fetch status data from the Automaton API.

**REQ-2.5.5**: The system SHALL format status information in a readable, structured format.

### 2.6 Help Command

**REQ-2.6.1**: The system SHALL respond to /help command with a list of available commands.

**REQ-2.6.2**: The system SHALL provide description and usage examples for each command.

**REQ-2.6.3**: The system SHALL include information about scheduled notification times.

**REQ-2.6.4**: The system SHALL explain the credit system and how to obtain more credits.

### 2.7 API Integration

**REQ-2.7.1**: The system SHALL communicate with Automaton API using HTTPS protocol.

**REQ-2.7.2**: The system SHALL include API key in Authorization header for all API requests.

**REQ-2.7.3**: The system SHALL set 30-second timeout for all API requests.

**REQ-2.7.4**: The system SHALL retry failed API requests up to 3 times with 2-second delays.

**REQ-2.7.5**: The system SHALL parse JSON responses from the Automaton API.

**REQ-2.7.6**: The system SHALL handle API error responses (4xx, 5xx) gracefully.

**REQ-2.7.7**: The system SHALL log all API requests and responses for debugging purposes.

### 2.8 Error Handling

**REQ-2.8.1**: The system SHALL remain operational when the Automaton API is unavailable.

**REQ-2.8.2**: The system SHALL send user-friendly error messages for all failure scenarios.

**REQ-2.8.3**: The system SHALL log all errors with timestamp, error type, and stack trace.

**REQ-2.8.4**: The system SHALL implement exponential backoff for Telegram API reconnection attempts.

**REQ-2.8.5**: The system SHALL handle Telegram API rate limiting with message queuing.

**REQ-2.8.6**: The system SHALL validate all user input before processing.

**REQ-2.8.7**: The system SHALL handle malformed commands with helpful usage instructions.

## 3. Non-Functional Requirements

### 3.1 Performance

**REQ-3.1.1**: The system SHALL respond to user commands within 2 seconds for 95% of requests.

**REQ-3.1.2**: The system SHALL complete notification delivery to 10,000 users within 5 minutes.

**REQ-3.1.3**: The system SHALL maintain memory usage below 512MB during normal operation.

**REQ-3.1.4**: The system SHALL support at least 1000 concurrent users.

**REQ-3.1.5**: The system SHALL process message queue at maximum rate allowed by Telegram API (30 msg/sec).

### 3.2 Reliability

**REQ-3.2.1**: The system SHALL achieve 99.5% uptime over any 30-day period.

**REQ-3.2.2**: The system SHALL automatically recover from Telegram API connection failures.

**REQ-3.2.3**: The system SHALL persist critical data to prevent loss during crashes.

**REQ-3.2.4**: The system SHALL implement health check endpoint for monitoring.

**REQ-3.2.5**: The system SHALL restart automatically on fatal errors (via Railway platform).

### 3.3 Security

**REQ-3.3.1**: The system SHALL store all sensitive credentials in environment variables.

**REQ-3.3.2**: The system SHALL never log sensitive user data (messages, personal information).

**REQ-3.3.3**: The system SHALL validate Telegram user IDs before processing requests.

**REQ-3.3.4**: The system SHALL sanitize user input to prevent injection attacks.

**REQ-3.3.5**: The system SHALL use HTTPS for all external API communications.

**REQ-3.3.6**: The system SHALL implement rate limiting per user to prevent abuse.

**REQ-3.3.7**: The system SHALL not expose internal error details to end users.

### 3.4 Maintainability

**REQ-3.4.1**: The system SHALL use ES modules (type: "module" in package.json).

**REQ-3.4.2**: The system SHALL follow consistent code formatting standards.

**REQ-3.4.3**: The system SHALL include inline comments for complex logic.

**REQ-3.4.4**: The system SHALL separate concerns into distinct modules (bot, API client, scheduler, handlers).

**REQ-3.4.5**: The system SHALL use meaningful variable and function names.

**REQ-3.4.6**: The system SHALL include README.md with setup and deployment instructions.

### 3.5 Scalability

**REQ-3.5.1**: The system SHALL use asynchronous I/O for all network operations.

**REQ-3.5.2**: The system SHALL implement connection pooling for API requests.

**REQ-3.5.3**: The system SHALL support horizontal scaling through stateless design.

**REQ-3.5.4**: The system SHALL cache frequently accessed data to reduce API calls.

**REQ-3.5.5**: The system SHALL implement message batching for notification delivery.

### 3.6 Deployment

**REQ-3.6.1**: The system SHALL be deployable to Railway platform with zero configuration.

**REQ-3.6.2**: The system SHALL read all configuration from environment variables.

**REQ-3.6.3**: The system SHALL include .gitignore file to exclude node_modules and sensitive files.

**REQ-3.6.4**: The system SHALL specify Node.js version in package.json engines field.

**REQ-3.6.5**: The system SHALL include start script in package.json for Railway deployment.

**REQ-3.6.6**: The system SHALL log startup information for deployment verification.

### 3.7 Monitoring and Logging

**REQ-3.7.1**: The system SHALL log all incoming user commands with timestamp and user ID.

**REQ-3.7.2**: The system SHALL log all API requests with method, URL, and response status.

**REQ-3.7.3**: The system SHALL log notification delivery statistics after each batch.

**REQ-3.7.4**: The system SHALL log errors with severity level (ERROR, WARN, INFO).

**REQ-3.7.5**: The system SHALL include correlation IDs for tracking request flows.

**REQ-3.7.6**: The system SHALL output logs in JSON format for structured logging.

**REQ-3.7.7**: The system SHALL support log level configuration via environment variable.

## 4. Data Requirements

### 4.1 Environment Variables

**REQ-4.1.1**: The system SHALL require TELEGRAM_BOT_TOKEN environment variable.

**REQ-4.1.2**: The system SHALL require AUTOMATON_API_URL environment variable.

**REQ-4.1.3**: The system SHALL require AUTOMATON_API_KEY environment variable.

**REQ-4.1.4**: The system SHALL support optional NODE_ENV environment variable (default: "production").

**REQ-4.1.5**: The system SHALL validate all required environment variables on startup.

**REQ-4.1.6**: The system SHALL fail fast with clear error message if required variables are missing.

### 4.2 Configuration

**REQ-4.2.1**: The system SHALL use hardcoded notification times (08:00, 14:00, 20:00 WIB).

**REQ-4.2.2**: The system SHALL use 30-second timeout for all API requests.

**REQ-4.2.3**: The system SHALL use 3 retry attempts for failed API requests.

**REQ-4.2.4**: The system SHALL use 2-second delay between retry attempts.

**REQ-4.2.5**: The system SHALL use Asia/Jakarta timezone for all scheduled tasks.

## 5. Interface Requirements

### 5.1 Telegram Bot Commands

**REQ-5.1.1**: The system SHALL support /start command for user registration.

**REQ-5.1.2**: The system SHALL support /status command for viewing user information.

**REQ-5.1.3**: The system SHALL support /help command for viewing available commands.

**REQ-5.1.4**: The system SHALL support /talk <message> command for AI conversation.

**REQ-5.1.5**: The system SHALL respond to unrecognized commands with help message.

### 5.2 Automaton API Endpoints

**REQ-5.2.1**: The system SHALL call POST /api/users/register for user registration.

**REQ-5.2.2**: The system SHALL call GET /api/users/{userId}/status for user status.

**REQ-5.2.3**: The system SHALL call POST /api/chat for conversation requests.

**REQ-5.2.4**: The system SHALL call GET /api/notifications for scheduled notification content.

**REQ-5.2.5**: The system SHALL include proper authentication headers in all API requests.

### 5.3 Message Formatting

**REQ-5.3.1**: The system SHALL support Markdown formatting in all bot messages.

**REQ-5.3.2**: The system SHALL use emojis to enhance message readability.

**REQ-5.3.3**: The system SHALL format credit amounts with thousand separators.

**REQ-5.3.4**: The system SHALL format timestamps in human-readable format.

**REQ-5.3.5**: The system SHALL limit message length to Telegram's 4096 character limit.

## 6. Quality Requirements

### 6.1 Testing

**REQ-6.1.1**: The system SHALL achieve minimum 80% code coverage.

**REQ-6.1.2**: The system SHALL include unit tests for all core functions.

**REQ-6.1.3**: The system SHALL include integration tests for end-to-end flows.

**REQ-6.1.4**: The system SHALL include property-based tests for critical invariants.

**REQ-6.1.5**: The system SHALL pass all tests before deployment.

### 6.2 Documentation

**REQ-6.2.1**: The system SHALL include README.md with project overview.

**REQ-6.2.2**: The system SHALL document all bot commands and their usage.

**REQ-6.2.3**: The system SHALL document deployment process to Railway.

**REQ-6.2.4**: The system SHALL document required environment variables.

**REQ-6.2.5**: The system SHALL document bot features and capabilities.

**REQ-6.2.6**: The system SHALL include inline code comments for complex logic.

## 7. Constraints

### 7.1 Technical Constraints

**CONSTRAINT-7.1.1**: The system MUST use Node.js 18 or higher.

**CONSTRAINT-7.1.2**: The system MUST use ES modules (not CommonJS).

**CONSTRAINT-7.1.3**: The system MUST use node-telegram-bot-api version 0.66.0 or higher.

**CONSTRAINT-7.1.4**: The system MUST use node-cron version 3.0.3 or higher.

**CONSTRAINT-7.1.5**: The system MUST use node-fetch version 3.3.2 or higher.

**CONSTRAINT-7.1.6**: The system MUST be deployable to Railway platform.

### 7.2 External Dependencies

**CONSTRAINT-7.2.1**: The system DEPENDS ON Telegram Bot API availability.

**CONSTRAINT-7.2.2**: The system DEPENDS ON Automaton API at https://automaton-production-a899.up.railway.app.

**CONSTRAINT-7.2.3**: The system DEPENDS ON stable internet connectivity.

**CONSTRAINT-7.2.4**: The system DEPENDS ON Railway platform for hosting.

### 7.3 Operational Constraints

**CONSTRAINT-7.3.1**: The system MUST respect Telegram API rate limits (30 messages/second).

**CONSTRAINT-7.3.2**: The system MUST operate within Railway's free tier limits (512MB RAM).

**CONSTRAINT-7.3.3**: The system MUST handle timezone conversions for WIB (UTC+7).

**CONSTRAINT-7.3.4**: The system MUST maintain backward compatibility with existing Automaton API.

## 8. Acceptance Criteria

### 8.1 Bot Functionality

**AC-8.1.1**: User can start bot with /start and receive welcome message with credits.

**AC-8.1.2**: User can check status with /status and see current credit balance.

**AC-8.1.3**: User can view help with /help and see all available commands.

**AC-8.1.4**: User can have conversation with /talk and receive AI responses.

**AC-8.1.5**: Bot sends automated notifications at scheduled times (08:00, 14:00, 20:00 WIB).

### 8.2 Error Handling

**AC-8.2.1**: Bot remains operational when Automaton API is down.

**AC-8.2.2**: Bot displays user-friendly error messages for all failures.

**AC-8.2.3**: Bot automatically reconnects after Telegram API disconnection.

**AC-8.2.4**: Bot handles invalid commands with helpful guidance.

**AC-8.2.5**: Bot continues notification delivery even if some users fail.

### 8.3 Deployment

**AC-8.3.1**: Bot can be deployed to Railway with provided instructions.

**AC-8.3.2**: Bot starts successfully with all required environment variables.

**AC-8.3.3**: Bot logs "Bot is ready" message on successful startup.

**AC-8.3.4**: Bot can be verified using Railway logs command.

**AC-8.3.5**: Bot responds to commands within 2 seconds of deployment.

### 8.4 Integration

**AC-8.4.1**: Bot successfully registers users with Automaton API.

**AC-8.4.2**: Bot successfully fetches user status from Automaton API.

**AC-8.4.3**: Bot successfully sends chat messages to Automaton API.

**AC-8.4.4**: Bot successfully fetches notification content from Automaton API.

**AC-8.4.5**: Bot includes correct API key in all requests.

## 9. Glossary

- **WIB**: Western Indonesian Time (UTC+7)
- **Polling**: Method of receiving updates from Telegram by repeatedly requesting new messages
- **Cron**: Time-based job scheduler for executing tasks at specific intervals
- **API Key**: Authentication token for accessing Automaton API
- **Credits**: Virtual currency used to pay for AI conversation services
- **Railway**: Cloud platform for deploying and hosting applications
- **ES Modules**: Modern JavaScript module system using import/export syntax
- **Idempotent**: Operation that produces same result regardless of how many times it's executed
- **Rate Limiting**: Restricting the number of requests within a time period
- **Exponential Backoff**: Retry strategy with progressively longer delays between attempts
