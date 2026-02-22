# Chef Agent API – Frontend Integration Guide

This guide documents the API routes for the frontend, including request bodies, response types, and usage notes.

**Base URL:** `/api/v1`

**Authentication:** All routes require a valid Auth0 Bearer token in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

---

## Table of Contents

1. [Chat Routes](#chat-routes)
2. [Thread Routes](#thread-routes)
3. [User Routes](#user-routes)
4. [Recipe Routes](#recipe-routes)
5. [Message Schema](#message-schema-used-in-threadout)
6. [Displaying Messages](#displaying-messages)

---

## Chat Routes

Base path: `POST /api/v1/chat`

### 1. Stream Chat

**Endpoint:** `POST /api/v1/chat/stream`

Streams the chef agent response via Server-Sent Events (SSE). Messages are automatically persisted to the database.

**Content-Type:** `multipart/form-data`

**Request Body (form fields):**

| Field           | Type   | Required | Description                                        |
| --------------- | ------ | -------- | -------------------------------------------------- |
| `thread_id`     | string | Yes      | Unique conversation thread identifier (UUID)       |
| `message`       | string | Yes      | Text message from the user                         |
| `image`         | File   | No       | Optional image (jpeg, png, webp, gif)              |
| `user_language` | string | No       | Preferred response language (default: `"English"`) |

**Example (JavaScript fetch):**

```javascript
const formData = new FormData();
formData.append("thread_id", "550e8400-e29b-41d4-a716-446655440000");
formData.append("message", "Suggest a pasta recipe for dinner");
formData.append("user_language", "Portuguese");
// Optional image:
formData.append("image", imageFile);

const response = await fetch("/api/v1/chat/stream", {
  method: "POST",
  headers: { Authorization: `Bearer ${accessToken}` },
  body: formData,
});

// Read SSE stream
const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = "";
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split("\n\n");
  buffer = lines.pop() || "";
  for (const chunk of lines) {
    if (chunk.startsWith("data: ")) {
      const json = JSON.parse(chunk.slice(6));
      handleSSEEvent(json);
    }
  }
}
```

**Response:** `text/event-stream` (SSE)

Each event is a JSON object prefixed with `data: ` and followed by `\n\n`.

**SSE Event Types (simplified for the recipe flow):**

| type     | Description                     | Payload                                  |
| -------- | ------------------------------- | ---------------------------------------- |
| `status` | Loading/status message for UI   | `{ type: "status", status: string }`     |
| `data`   | Text chunk from the assistant   | `{ type: "data", data: string }`         |
| `recipe` | AI generated a recipe (once)    | `{ type: "recipe", recipes: [ {...} ] }` |

Recipe data is delivered only via the **`recipe`** event. The frontend does not need to parse `tool_result` for recipes. The backend does **not** auto-create the recipe; the frontend should create/save the recipe (e.g. via the recipe API) when it receives the **`recipe`** event.

**Status events** – sent only when the message is creating a recipe:

1. **`status`** – `"Creating your recipe..."` – when recipe generation starts (when the agent calls the chef).
2. Then **`data`** (assistant text) and **`recipe`** (one event with the generated recipe).

No status is sent for non-recipe messages (e.g. greetings, chat). Handle in your SSE loop: `if (json.type === 'status') { setLoadingMessage(json.status); }` and `if (json.type === 'recipe') { setRecipes(json.recipes); }` (then create/save the recipe via your API if needed).

---

## Thread Routes

Base path: `/api/v1/thread`

### 1. Create Thread

**Endpoint:** `POST /api/v1/thread/`

Creates a new conversation thread for the current user.

**Request Body:** None

**Response:** `201 Created`

```typescript
interface ThreadOut {
  id: string; // UUID
  user_id: number;
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
  messages: MessageOut[];
}
```

**Example response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "created_at": "2025-02-21T12:00:00.000Z",
  "updated_at": "2025-02-21T12:00:00.000Z",
  "messages": []
}
```

---

### 2. List Threads

**Endpoint:** `GET /api/v1/thread/`

Returns all threads for the current user.

**Request Body:** None

**Response:** `200 OK`

```typescript
type Response = ThreadOut[];
```

---

### 3. Get Thread by ID

**Endpoint:** `GET /api/v1/thread/{thread_id}`

**Path Parameters:** `thread_id` – UUID

**Request Body:** None

**Response:** `200 OK` – `ThreadOut`

**Errors:**

| Status | Detail           |
| ------ | ---------------- |
| 404    | Thread not found |

---

### 4. Delete Thread

**Endpoint:** `DELETE /api/v1/thread/{thread_id}`

**Path Parameters:** `thread_id` – UUID

**Request Body:** None

**Response:** `204 No Content` (success)

**Errors:**

| Status | Detail           |
| ------ | ---------------- |
| 404    | Thread not found |

---

## User Routes

Base path: `/api/v1/user`

### 1. Get Current User

**Endpoint:** `GET /api/v1/user/me`

Returns the currently authenticated user.

**Request Body:** None

**Response:** `200 OK`

```typescript
interface UserOut {
  id: number;
  auth0_id: string;
  email: string;
  name: string | null;
  surname: string | null;
  img: string | null;
}
```

---

### 2. Update Current User

**Endpoint:** `PATCH /api/v1/user/me`

Updates the current user's profile. All fields are optional (partial update).

**Content-Type:** `application/json`

**Request Body:**

```typescript
interface UserUpdate {
  email?: string; // Must be valid email; may be restricted for OAuth users
  name?: string;
  surname?: string;
  img?: string;
}
```

**Example:**

```json
{
  "name": "John",
  "surname": "Doe"
}
```

**Response:** `200 OK` – `UserOut`

**Errors:**

| Status | Detail                                                                   |
| ------ | ------------------------------------------------------------------------ |
| 400    | Email already in use                                                     |
| 400    | Auth0 rejected email change                                              |
| 400    | Account managed by external provider; update email via identity provider |
| 404    | User not found                                                           |

---

## Recipe Routes

Base path: `/api/v1/recipes`

### Shared Schemas

```typescript
interface IngredientItem {
  name: string;
  quantity: string; // e.g. "2 cups", "200g", "1 tbsp"
}

interface InstructionStep {
  step_number: number; // 1-based
  description: string;
  time_minutes: number; // >= 0
  chef_tip?: string; // Optional
}

interface Recipe {
  id: string; // UUID
  name: string;
  description: string;
  prep_time: number;
  cook_time: number;
  total_time: number;
  servings: number;
  difficulty: string;
  ingredients: IngredientItem[];
  instructions: InstructionStep[];
  tags: string[];
  image_url?: string;
  created_at?: string; // ISO 8601 datetime
  updated_at?: string; // ISO 8601 datetime
}
```

---

### 1. Create Recipe

**Endpoint:** `POST /api/v1/recipes/`

**Content-Type:** `application/json`

**Request Body:**

```typescript
interface RecipeCreate {
  name: string;
  description: string;
  prep_time: number;
  cook_time: number;
  total_time: number;
  servings: number;
  difficulty: string;
  ingredients: IngredientItem[];
  instructions: InstructionStep[];
  tags?: string[]; // Optional, default []
  image_url?: string; // Optional
}
```

**Example:**

```json
{
  "name": "Spaghetti Carbonara",
  "description": "Classic Italian pasta",
  "prep_time": 15,
  "cook_time": 20,
  "total_time": 35,
  "servings": 4,
  "difficulty": "medium",
  "ingredients": [
    { "name": "spaghetti", "quantity": "400g" },
    { "name": "guanciale", "quantity": "200g" }
  ],
  "instructions": [
    {
      "step_number": 1,
      "description": "Boil water and cook pasta",
      "time_minutes": 10,
      "chef_tip": "Salt the water generously"
    }
  ],
  "tags": ["pasta", "italian"]
}
```

**Response:** `201 Created` – `Recipe`

---

### 2. List Recipes

**Endpoint:** `GET /api/v1/recipes/`

Returns all recipes for the current user.

**Request Body:** None

**Response:** `200 OK`

```typescript
type Response = Recipe[];
```

---

### 3. Get Recipe by ID

**Endpoint:** `GET /api/v1/recipes/{recipe_id}`

**Path Parameters:** `recipe_id` – UUID

**Request Body:** None

**Response:** `200 OK` – `Recipe`

**Errors:**

| Status | Detail           |
| ------ | ---------------- |
| 404    | Recipe not found |

---

### 4. Update Recipe (Partial)

**Endpoint:** `PATCH /api/v1/recipes/{recipe_id}`

**Path Parameters:** `recipe_id` – UUID

**Content-Type:** `application/json`

**Request Body:** All fields optional

```typescript
interface RecipeUpdate {
  name?: string;
  description?: string;
  prep_time?: number;
  cook_time?: number;
  total_time?: number;
  servings?: number;
  difficulty?: string;
  ingredients?: IngredientItem[];
  instructions?: InstructionStep[];
  tags?: string[];
  image_url?: string;
}
```

**Example:**

```json
{
  "servings": 6,
  "tags": ["pasta", "italian", "quick"]
}
```

**Response:** `200 OK` – `Recipe`

---

### 5. Delete Recipe

**Endpoint:** `DELETE /api/v1/recipes/{recipe_id}`

**Path Parameters:** `recipe_id` – UUID

**Request Body:** None

**Response:** `204 No Content` (success)

---

## Message Schema (used in ThreadOut)

```typescript
interface MessageOut {
  id: string; // UUID
  content: string;
  role: "user" | "assistant";
  thread_id: string; // UUID
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
}
```

---

## Displaying Messages

This section explains how the frontend should display messages, including when recipe data is available (during streaming) vs when loading thread history.

### Two contexts

| Context | Source | Recipe data available? |
| ------- | ------ | ---------------------- |
| **Streaming** | SSE events from `POST /chat/stream` | Yes – in `recipe` event and persisted message |
| **Thread history** | `GET /thread/{id}` or `GET /message/thread/{thread_id}` | Yes – `content` (text) + `recipes` (when recipe was created) |

---

### During streaming (live chat)

While consuming the SSE stream, the frontend should handle events as follows:

#### 0. Status events (loading, recipe flow only)

- **Event:** `{ type: "status", status: string }`
- **When:** Sent only when the message is creating a recipe (when the agent starts generating a recipe).
- **Display:** Use `status` as the loading message (e.g. spinner + "Creating your recipe..."). Clear when you receive `data` or `recipe` content.
- Typical value: `"Creating your recipe..."`. No status events are sent for non-recipe messages (e.g. greetings, chat).

#### 1. Text content (`data` events)

- **Event:** `{ type: "data", data: string, thread_id?: string }`
- **Display:** Append `data` to the current assistant message and render the accumulated text in real time (e.g. as markdown).
- Messages are persisted automatically; the concatenated text is stored when the stream finishes.

#### 2. Recipe data (`recipe` event)

- **Event:** `{ type: "recipe", recipes: [ {...} ] }`
- **When:** Sent once when the AI generates a recipe (one recipe per request). The backend does not auto-create/save the recipe; the frontend should create or save it (e.g. via the recipe API) when it receives this event.
- **Display:** Use `recipes` to render **recipe cards** (name, ingredients, instructions, image, times, etc.). Show recipe cards in addition to the assistant text.

Recipe object shape (normalized; one item in the array):

```typescript
interface RecipeFromStream {
  name: string;
  description?: string;
  prep_time?: number;
  cook_time?: number;
  total_time?: number;
  servings?: number;
  difficulty?: string;
  ingredients: Array<{ name: string; quantity: string }>;
  instructions: Array<{
    step_number: number;
    description: string;
    time_minutes: number;
    chef_tip?: string;
  }>;
  tags?: string[];
  image_url?: string;
}
```

Example flow:

1. Append `data` events to the assistant bubble.
2. On `recipe` event → use `event.recipes` to render recipe cards.

---

### Thread history (GET thread / messages)

When loading a thread via `GET /api/v1/thread/{thread_id}` or `GET /api/v1/message/thread/{thread_id}`:

- Each message has `content: string`, `role: "user" | "assistant"`, and optionally `recipes: array | null`.
- **User messages:** Plain text (and optional image during send). Images are not stored; display text only.
- **Assistant messages:** `content` is the assistant’s text. When the assistant replied with a recipe, the API also persists `recipes` (array of recipe objects) on the message so the UI can render recipe cards on refresh without storing them locally.

**Implication:** For thread history, render assistant messages with `content` as the main text and, when `recipes` is present, render recipe cards from `recipes` (same shape as in the stream’s `recipe` event).

---

### Suggested UI patterns

| Scenario | Display |
| -------- | ------- |
| User message | Text bubble; optional image thumbnail if sent (only during that request, not in history) |
| Assistant text | Markdown-rendered text in a chat bubble |
| Recipes from `recipe` event | Recipe cards (name, image, ingredients, instructions, time) below the assistant text |
| Thread history (user) | Text only |
| Thread history (assistant) | Text + optional `recipes` array for recipe cards (persisted by API) |

---

## Common Error Response

On error, the API returns:

```json
{
  "detail": "Error message"
}
```

For validation errors (422):

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "validation error message",
      "type": "value_error.xxx"
    }
  ]
}
```

---

## Swagger / OpenAPI

Interactive API docs are available at:

- **Swagger UI:** `GET /api/v1/docs`
- **OpenAPI JSON:** `GET /api/v1/openapi.json`

These support OAuth2 with Auth0 for testing protected endpoints.
