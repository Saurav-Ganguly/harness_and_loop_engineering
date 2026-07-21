# Ollama Docs (scraped reference)

Source: https://docs.ollama.com/llms.txt  |  Scraped for the harness build.
Sections: Authentication, Cloud, Chat API, Generate API, Streaming, Tool Calling, Structured Outputs, OpenAI Compatibility.


---

# Authentication

No authentication is required when accessing Ollama's API locally via `http://localhost:11434`.

Authentication is required for the following:

* Running cloud models via ollama.com
* Publishing models
* Downloading private models

Ollama supports two authentication methods:

* **Signing in**: sign in from your local installation, and Ollama will automatically take care of authenticating requests to ollama.com when running commands
* **API keys**: API keys for programmatic access to ollama.com's API

## Signing in

To sign in to ollama.com from your local installation of Ollama, run:

```
ollama signin
```

Once signed in, Ollama will automatically authenticate commands as required:

```
ollama run gpt-oss:120b-cloud
```

Similarly, when accessing a local API endpoint that requires cloud access, Ollama will automatically authenticate the request:

```shell theme={"system"}
curl http://localhost:11434/api/generate -d '{
  "model": "gpt-oss:120b-cloud",
  "prompt": "Why is the sky blue?"
}'
```

## API keys

For direct access to ollama.com's API served at `https://ollama.com/api`, authentication via API keys is required.

First, create an [API key](https://ollama.com/settings/keys), then set the `OLLAMA_API_KEY` environment variable:

```shell theme={"system"}
export OLLAMA_API_KEY=your_api_key
```

Then use the API key in the Authorization header:

```shell theme={"system"}
curl https://ollama.com/api/generate \
  -H "Authorization: Bearer $OLLAMA_API_KEY" \
  -d '{
    "model": "gpt-oss:120b",
    "prompt": "Why is the sky blue?",
    "stream": false
  }'
```

API keys don't currently expire, however you can revoke them at any time in your [API keys settings](https://ollama.com/settings/keys).

---

# Cloud

## Cloud Models

Ollama's cloud models are a new kind of model in Ollama that can run without a powerful GPU. Instead, cloud models are automatically offloaded to Ollama's cloud service while offering the same capabilities as local models, making it possible to keep using your local tools while running larger models that wouldn't fit on a personal computer.

### Supported models

For a list of supported models, see Ollama's [model library](https://ollama.com/search?c=cloud).

### Running Cloud models

Ollama's cloud models require an account on [ollama.com](https://ollama.com). To sign in or create an account, run:

```
ollama signin
```

<Tabs>
  <Tab title="CLI">
    To run a cloud model, open the terminal and run:

    ```
    ollama run gpt-oss:120b-cloud
    ```
  </Tab>

  <Tab title="Python">
    First, pull a cloud model so it can be accessed:

    ```
    ollama pull gpt-oss:120b-cloud
    ```

    Next, install [Ollama's Python library](https://github.com/ollama/ollama-python):

    ```
    pip install ollama
    ```

    Next, create and run a simple Python script:

    ```python theme={"system"}
    from ollama import Client

    client = Client()

    messages = [
      {
        'role': 'user',
        'content': 'Why is the sky blue?',
      },
    ]

    for part in client.chat('gpt-oss:120b-cloud', messages=messages, stream=True):
      print(part['message']['content'], end='', flush=True)
    ```
  </Tab>

  <Tab title="JavaScript">
    First, pull a cloud model so it can be accessed:

    ```
    ollama pull gpt-oss:120b-cloud
    ```

    Next, install [Ollama's JavaScript library](https://github.com/ollama/ollama-js):

    ```
    npm i ollama
    ```

    Then use the library to run a cloud model:

    ```typescript theme={"system"}
    import { Ollama } from "ollama";

    const ollama = new Ollama();

    const response = await ollama.chat({
      model: "gpt-oss:120b-cloud",
      messages: [{ role: "user", content: "Explain quantum computing" }],
      stream: true,
    });

    for await (const part of response) {
      process.stdout.write(part.message.content);
    }
    ```
  </Tab>

  <Tab title="cURL">
    First, pull a cloud model so it can be accessed:

    ```
    ollama pull gpt-oss:120b-cloud
    ```

    Run the following cURL command to run the command via Ollama's API:

    ```
    curl http://localhost:11434/api/chat -d '{
      "model": "gpt-oss:120b-cloud",
      "messages": [{
        "role": "user",
        "content": "Why is the sky blue?"
      }],
      "stream": false
    }'
    ```
  </Tab>
</Tabs>

## Cloud API access

Cloud models can also be accessed directly on ollama.com's API. In this mode, ollama.com acts as a remote Ollama host.

### Authentication

For direct access to ollama.com's API, first create an [API key](https://ollama.com/settings/keys).

Then, set the `OLLAMA_API_KEY` environment variable to your API key.

```
export OLLAMA_API_KEY=your_api_key
```

### Listing models

For models available directly via Ollama's API, models can be listed via:

```
curl https://ollama.com/api/tags
```

### Generating a response

<Tabs>
  <Tab title="Python">
    First, install [Ollama's Python library](https://github.com/ollama/ollama-python)

    ```
    pip install ollama
    ```

    Then make a request

    ```python theme={"system"}
    import os
    from ollama import Client

    client = Client(
        host="https://ollama.com",
        headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')}
    )

    messages = [
      {
        'role': 'user',
        'content': 'Why is the sky blue?',
      },
    ]

    for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
      print(part['message']['content'], end='', flush=True)
    ```
  </Tab>

  <Tab title="JavaScript">
    First, install [Ollama's JavaScript library](https://github.com/ollama/ollama-js):

    ```
    npm i ollama
    ```

    Next, make a request to the model:

    ```typescript theme={"system"}
    import { Ollama } from "ollama";

    const ollama = new Ollama({
      host: "https://ollama.com",
      headers: {
        Authorization: "Bearer " + process.env.OLLAMA_API_KEY,
      },
    });

    const response = await ollama.chat({
      model: "gpt-oss:120b",
      messages: [{ role: "user", content: "Explain quantum computing" }],
      stream: true,
    });

    for await (const part of response) {
      process.stdout.write(part.message.content);
    }
    ```
  </Tab>

  <Tab title="cURL">
    Generate a response via Ollama's chat API:

    ```
    curl https://ollama.com/api/chat \
      -H "Authorization: Bearer $OLLAMA_API_KEY" \
      -d '{
        "model": "gpt-oss:120b",
        "messages": [{
          "role": "user",
          "content": "Why is the sky blue?"
        }],
        "stream": false
      }'
    ```
  </Tab>
</Tabs>

## Local only

Ollama can run in local-only mode by [disabling Ollama's cloud](./faq#how-do-i-disable-ollama-cloud) features.

## Retirements

Ollama will occasionally deprecate and retire older cloud models as newer and better open-source models are released.
Tools and applications relying on Ollama Cloud models may need to be updated to keep working. Impacted users will be
notified in advance of model deprecation and retirement. Deprecations will be communicated through email and on the
Ollama website.

Ollama Cloud model retirement does not affect local models.

### Upcoming retirements

| Retirement date | Model                    | Recommended alternative |
| --------------- | ------------------------ | ----------------------- |
| July 15, 2026   | `deepseek-v3.1:671b`     | `deepseek-v4-flash`     |
| July 15, 2026   | `deepseek-v3.2`          | `deepseek-v4-flash`     |
| July 15, 2026   | `devstral-2:123b`        | `mistral-large-3:675b`  |
| July 15, 2026   | `devstral-small-2:24b`   |                         |
| July 15, 2026   | `ministral-3:14b`        |                         |
| July 15, 2026   | `ministral-3:3b`         |                         |
| July 15, 2026   | `ministral-3:8b`         |                         |
| July 15, 2026   | `gemini-3-flash-preview` | `minimax-m3`            |
| July 15, 2026   | `gemma3:12b`             | `gemma4:31b`            |
| July 15, 2026   | `gemma3:27b`             | `gemma4:31b`            |
| July 15, 2026   | `gemma3:4b`              | `gemma4:31b`            |
| July 15, 2026   | `glm-4.7`                | `glm-5.2`               |
| July 15, 2026   | `glm-5`                  | `glm-5.2`               |
| July 15, 2026   | `minimax-m2.1`           | `minimax-m3`            |
| July 15, 2026   | `qwen3-coder-next`       | `qwen3.5:397b`          |
| July 15, 2026   | `qwen3-coder:480b`       | `qwen3.5:397b`          |

### Past retirements

<AccordionGroup>
  <Accordion title="June 30, 2026">
    | Model      | Recommended alternative |
    | ---------- | ----------------------- |
    | `rnj-1:8b` |                         |
  </Accordion>

  <Accordion title="June 16, 2026">
    | Model                    | Recommended alternative |
    | ------------------------ | ----------------------- |
    | `kimi-k2-thinking`       | `kimi-k2.6`             |
    | `kimi-k2:1t`             | `kimi-k2.6`             |
    | `minimax-m2`             | `minimax-m3`            |
    | `glm-4.6`                | `glm-5.1`               |
    | `qwen3-next:80b`         | `qwen3.5`               |
    | `qwen3-vl:235b`          | `qwen3.5`               |
    | `qwen3-vl:235b-instruct` | `qwen3.5`               |
    | `cogito-2.1:671b`        | `deepseek-v4-flash`     |
  </Accordion>
</AccordionGroup>

---

# Generate a chat message

> Generate the next chat message in a conversation between a user and an assistant.



## OpenAPI

````yaml /openapi.yaml post /api/chat
openapi: 3.1.0
info:
  title: Ollama API
  version: 0.1.0
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT
  description: |
    OpenAPI specification for the Ollama HTTP API
servers:
  - url: http://localhost:11434
    description: Ollama
security: []
paths:
  /api/chat:
    post:
      summary: Generate a chat message
      description: >-
        Generate the next chat message in a conversation between a user and an
        assistant.
      operationId: chat
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChatRequest'
      responses:
        '200':
          description: Chat response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ChatResponse'
              example:
                model: gemma4
                created_at: '2025-10-17T23:14:07.414671Z'
                message:
                  role: assistant
                  content: Hello! How can I help you today?
                done: true
                done_reason: stop
                total_duration: 174560334
                load_duration: 101397084
                prompt_eval_count: 11
                prompt_eval_duration: 13074791
                eval_count: 18
                eval_duration: 52479709
            application/x-ndjson:
              schema:
                $ref: '#/components/schemas/ChatStreamEvent'
      x-codeSamples:
        - lang: bash
          label: Default
          source: |
            curl http://localhost:11434/api/chat -d '{
              "model": "gemma4",
              "messages": [
                {
                  "role": "user",
                  "content": "why is the sky blue?"
                }
              ]
            }'
        - lang: bash
          label: Non-streaming
          source: |
            curl http://localhost:11434/api/chat -d '{
              "model": "gemma4",
              "messages": [
                {
                  "role": "user",
                  "content": "why is the sky blue?"
                }
              ],
              "stream": false
            }'
        - lang: bash
          label: Structured outputs
          source: >
            curl -X POST http://localhost:11434/api/chat -H "Content-Type:
            application/json" -d '{
              "model": "gemma4",
              "messages": [
                {
                  "role": "user",
                  "content": "What are the populations of the United States and Canada?"
                }
              ],
              "stream": false,
              "format": {
                "type": "object",
                "properties": {
                  "countries": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "country": {"type": "string"},
                        "population": {"type": "integer"}
                      },
                      "required": ["country", "population"]
                    }
                  }
                },
                "required": ["countries"]
              }
            }'
        - lang: bash
          label: Tool calling
          source: |
            curl http://localhost:11434/api/chat -d '{
              "model": "qwen3",
              "messages": [
                {
                  "role": "user",
                  "content": "What is the weather today in Paris?"
                }
              ],
              "stream": false,
              "tools": [
                {
                  "type": "function",
                  "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather for a location",
                    "parameters": {
                      "type": "object",
                      "properties": {
                        "location": {
                          "type": "string",
                          "description": "The location to get the weather for, e.g. San Francisco, CA"
                        },
                        "format": {
                          "type": "string",
                          "description": "The format to return the weather in, e.g. 'celsius' or 'fahrenheit'",
                          "enum": ["celsius", "fahrenheit"]
                        }
                      },
                      "required": ["location", "format"]
                    }
                  }
                }
              ]
            }'
        - lang: bash
          label: Thinking
          source: |
            curl http://localhost:11434/api/chat -d '{
              "model": "gpt-oss",
              "messages": [
                {
                  "role": "user",
                  "content": "What is 1+1?"
                }
              ],
              "think": "low"
            }'
        - lang: bash
          label: Images
          source: |
            curl http://localhost:11434/api/chat -d '{
              "model": "gemma4",
              "messages": [
                {
                  "role": "user",
                  "content": "What is in this image?",
                  "images": [
                    "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"
                  ]
                }
              ]
            }'
components:
  schemas:
    ChatRequest:
      type: object
      required:
        - model
        - messages
      properties:
        model:
          type: string
          description: Model name
        messages:
          type: array
          description: >-
            Chat history as an array of message objects (each with a role and
            content)
          items:
            $ref: '#/components/schemas/ChatMessage'
        tools:
          type: array
          description: Optional list of function tools the model may call during the chat
          items:
            $ref: '#/components/schemas/ToolDefinition'
        format:
          oneOf:
            - type: string
              enum:
                - json
            - type: object
          description: Format to return a response in. Can be `json` or a JSON schema
        options:
          $ref: '#/components/schemas/ModelOptions'
        stream:
          type: boolean
          default: true
        think:
          oneOf:
            - type: boolean
            - type: string
              enum:
                - high
                - medium
                - low
                - max
          description: >-
            When true, returns separate thinking output in addition to content.
            Can be a boolean (true/false) or a string ("high", "medium", "low",
            "max") for supported models, with "max" requesting the highest
            thinking level.
        keep_alive:
          oneOf:
            - type: string
            - type: number
          description: >-
            Model keep-alive duration (for example `5m` or `0` to unload
            immediately)
        logprobs:
          type: boolean
          description: Whether to return log probabilities of the output tokens
        top_logprobs:
          type: integer
          description: >-
            Number of most likely tokens to return at each token position when
            logprobs are enabled
    ChatResponse:
      type: object
      properties:
        model:
          type: string
          description: Model name used to generate this message
        created_at:
          type: string
          format: date-time
          description: Timestamp of response creation (ISO 8601)
        message:
          type: object
          properties:
            role:
              type: string
              enum:
                - assistant
              description: Always `assistant` for model responses
            content:
              type: string
              description: Assistant message text
            thinking:
              type: string
              description: Optional deliberate thinking trace when `think` is enabled
            tool_calls:
              type: array
              items:
                $ref: '#/components/schemas/ToolCall'
              description: Tool calls requested by the assistant
            images:
              type: array
              items:
                type: string
              description: Optional base64-encoded images in the response
        done:
          type: boolean
          description: Indicates whether the chat response has finished
        done_reason:
          type: string
          description: Reason the response finished
        total_duration:
          type: integer
          description: Total time spent generating in nanoseconds
        load_duration:
          type: integer
          description: Time spent loading the model in nanoseconds
        prompt_eval_count:
          type: integer
          description: Number of tokens in the prompt
        prompt_eval_duration:
          type: integer
          description: Time spent evaluating the prompt in nanoseconds
        eval_count:
          type: integer
          description: Number of tokens generated in the response
        eval_duration:
          type: integer
          description: Time spent generating tokens in nanoseconds
        logprobs:
          type: array
          items:
            $ref: '#/components/schemas/Logprob'
          description: >-
            Log probability information for the generated tokens when logprobs
            are enabled
    ChatStreamEvent:
      type: object
      properties:
        model:
          type: string
          description: Model name used for this stream event
        created_at:
          type: string
          format: date-time
          description: When this chunk was created (ISO 8601)
        message:
          type: object
          properties:
            role:
              type: string
              description: Role of the message for this chunk
            content:
              type: string
              description: Partial assistant message text
            thinking:
              type: string
              description: Partial thinking text when `think` is enabled
            tool_calls:
              type: array
              items:
                $ref: '#/components/schemas/ToolCall'
              description: Partial tool calls, if any
            images:
              type: array
              items:
                type: string
              description: Partial base64-encoded images, when present
        done:
          type: boolean
          description: True for the final event in the stream
    ChatMessage:
      type: object
      required:
        - role
        - content
      properties:
        role:
          type: string
          enum:
            - system
            - user
            - assistant
            - tool
          description: Author of the message.
        content:
          type: string
          description: Message text content
        images:
          type: array
          items:
            type: string
            description: Base64-encoded image content
          description: Optional list of inline images for multimodal models
        tool_calls:
          type: array
          items:
            $ref: '#/components/schemas/ToolCall'
          description: Tool call requests produced by the model
    ToolDefinition:
      type: object
      required:
        - type
        - function
      properties:
        type:
          type: string
          enum:
            - function
          description: Type of tool (always `function`)
        function:
          type: object
          required:
            - name
            - parameters
          properties:
            name:
              type: string
              description: Function name exposed to the model
            description:
              type: string
              description: Human-readable description of the function
            parameters:
              type: object
              description: JSON Schema for the function parameters
    ModelOptions:
      type: object
      description: Runtime options that control text generation
      properties:
        seed:
          type: integer
          description: Random seed used for reproducible outputs
        temperature:
          type: number
          format: float
          description: Controls randomness in generation (higher = more random)
        top_k:
          type: integer
          description: Limits next token selection to the K most likely
        top_p:
          type: number
          format: float
          description: Cumulative probability threshold for nucleus sampling
        min_p:
          type: number
          format: float
          description: Minimum probability threshold for token selection
        stop:
          oneOf:
            - type: string
            - type: array
              items:
                type: string
          description: Stop sequences that will halt generation
        num_ctx:
          type: integer
          description: Context length size (number of tokens)
        num_predict:
          type: integer
          description: Maximum number of tokens to generate
      additionalProperties: true
    ToolCall:
      type: object
      properties:
        function:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              description: Name of the function to call
            description:
              type: string
              description: What the function does
            arguments:
              type: object
              description: JSON object of arguments to pass to the function
    Logprob:
      type: object
      description: Log probability information for a generated token
      properties:
        token:
          type: string
          description: The text representation of the token
        logprob:
          type: number
          description: The log probability of this token
        bytes:
          type: array
          items:
            type: integer
          description: The raw byte representation of the token
        top_logprobs:
          type: array
          items:
            $ref: '#/components/schemas/TokenLogprob'
          description: Most likely tokens and their log probabilities at this position
    TokenLogprob:
      type: object
      description: Log probability information for a single token alternative
      properties:
        token:
          type: string
          description: The text representation of the token
        logprob:
          type: number
          description: The log probability of this token
        bytes:
          type: array
          items:
            type: integer
          description: The raw byte representation of the token

````

---

# Generate a response

> Generates a response for the provided prompt



## OpenAPI

````yaml /openapi.yaml post /api/generate
openapi: 3.1.0
info:
  title: Ollama API
  version: 0.1.0
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT
  description: |
    OpenAPI specification for the Ollama HTTP API
servers:
  - url: http://localhost:11434
    description: Ollama
security: []
paths:
  /api/generate:
    post:
      summary: Generate a response
      description: Generates a response for the provided prompt
      operationId: generate
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateRequest'
            example:
              model: gemma4
              prompt: Why is the sky blue?
      responses:
        '200':
          description: Generation responses
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GenerateResponse'
              example:
                model: gemma4
                created_at: '2025-10-17T23:14:07.414671Z'
                response: Hello! How can I help you today?
                done: true
                done_reason: stop
                total_duration: 174560334
                load_duration: 101397084
                prompt_eval_count: 11
                prompt_eval_duration: 13074791
                eval_count: 18
                eval_duration: 52479709
            application/x-ndjson:
              schema:
                $ref: '#/components/schemas/GenerateStreamEvent'
      x-codeSamples:
        - lang: bash
          label: Default
          source: |
            curl http://localhost:11434/api/generate -d '{
              "model": "gemma4",
              "prompt": "Why is the sky blue?"
            }'
        - lang: bash
          label: Non-streaming
          source: |
            curl http://localhost:11434/api/generate -d '{
              "model": "gemma4",
              "prompt": "Why is the sky blue?",
              "stream": false
            }'
        - lang: bash
          label: With options
          source: |
            curl http://localhost:11434/api/generate -d '{
              "model": "gemma4",
              "prompt": "Why is the sky blue?",
              "options": {
                "temperature": 0.8,
                "top_p": 0.9,
                "seed": 42
              }
            }'
        - lang: bash
          label: Structured outputs
          source: |
            curl http://localhost:11434/api/generate -d '{
              "model": "gemma4",
              "prompt": "What are the populations of the United States and Canada?",
              "stream": false,
              "format": {
                "type": "object",
                "properties": {
                  "countries": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "country": {"type": "string"},
                        "population": {"type": "integer"}
                      },
                      "required": ["country", "population"]
                    }
                  }
                },
                "required": ["countries"]
              }
            }'
        - lang: bash
          label: With images
          source: |
            curl http://localhost:11434/api/generate -d '{
              "model": "gemma4",
              "prompt": "What is in this picture?",
              "images": ["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"]
            }'
        - lang: bash
          label: Load model
          source: |
            curl http://localhost:11434/api/generate -d '{
              "model": "gemma4"
            }'
        - lang: bash
          label: Unload model
          source: |
            curl http://localhost:11434/api/generate -d '{
              "model": "gemma4",
              "keep_alive": 0
            }'
components:
  schemas:
    GenerateRequest:
      type: object
      required:
        - model
      properties:
        model:
          type: string
          description: Model name
        prompt:
          type: string
          description: Text for the model to generate a response from
        suffix:
          type: string
          description: >-
            Used for fill-in-the-middle models, text that appears after the user
            prompt and before the model response
        images:
          type: array
          items:
            type: string
            description: Base64-encoded images for models that support image input
        format:
          description: >-
            Structured output format for the model to generate a response from.
            Supports either the string `"json"` or a JSON schema object.
          oneOf:
            - type: string
            - type: object
        system:
          description: System prompt for the model to generate a response from
          type: string
        stream:
          description: When true, returns a stream of partial responses
          type: boolean
          default: true
        think:
          oneOf:
            - type: boolean
            - type: string
              enum:
                - high
                - medium
                - low
                - max
          description: >-
            When true, returns separate thinking output in addition to content.
            Can be a boolean (true/false) or a string ("high", "medium", "low",
            "max") for supported models, with "max" requesting the highest
            thinking level.
        raw:
          type: boolean
          description: >-
            When true, returns the raw response from the model without any
            prompt templating
        keep_alive:
          oneOf:
            - type: string
            - type: number
          description: >-
            Model keep-alive duration (for example `5m` or `0` to unload
            immediately)
        options:
          $ref: '#/components/schemas/ModelOptions'
        logprobs:
          type: boolean
          description: Whether to return log probabilities of the output tokens
        top_logprobs:
          type: integer
          description: >-
            Number of most likely tokens to return at each token position when
            logprobs are enabled
    GenerateResponse:
      type: object
      properties:
        model:
          type: string
          description: Model name
        created_at:
          type: string
          description: ISO 8601 timestamp of response creation
        response:
          type: string
          description: The model's generated text response
        thinking:
          type: string
          description: The model's generated thinking output
        done:
          type: boolean
          description: Indicates whether generation has finished
        done_reason:
          type: string
          description: Reason the generation stopped
        total_duration:
          type: integer
          description: Time spent generating the response in nanoseconds
        load_duration:
          type: integer
          description: Time spent loading the model in nanoseconds
        prompt_eval_count:
          type: integer
          description: Number of input tokens in the prompt
        prompt_eval_duration:
          type: integer
          description: Time spent evaluating the prompt in nanoseconds
        eval_count:
          type: integer
          description: Number of output tokens generated in the response
        eval_duration:
          type: integer
          description: Time spent generating tokens in nanoseconds
        logprobs:
          type: array
          items:
            $ref: '#/components/schemas/Logprob'
          description: >-
            Log probability information for the generated tokens when logprobs
            are enabled
    GenerateStreamEvent:
      type: object
      properties:
        model:
          type: string
          description: Model name
        created_at:
          type: string
          description: ISO 8601 timestamp of response creation
        response:
          type: string
          description: The model's generated text response for this chunk
        thinking:
          type: string
          description: The model's generated thinking output for this chunk
        done:
          type: boolean
          description: Indicates whether the stream has finished
        done_reason:
          type: string
          description: Reason streaming finished
        total_duration:
          type: integer
          description: Time spent generating the response in nanoseconds
        load_duration:
          type: integer
          description: Time spent loading the model in nanoseconds
        prompt_eval_count:
          type: integer
          description: Number of input tokens in the prompt
        prompt_eval_duration:
          type: integer
          description: Time spent evaluating the prompt in nanoseconds
        eval_count:
          type: integer
          description: Number of output tokens generated in the response
        eval_duration:
          type: integer
          description: Time spent generating tokens in nanoseconds
    ModelOptions:
      type: object
      description: Runtime options that control text generation
      properties:
        seed:
          type: integer
          description: Random seed used for reproducible outputs
        temperature:
          type: number
          format: float
          description: Controls randomness in generation (higher = more random)
        top_k:
          type: integer
          description: Limits next token selection to the K most likely
        top_p:
          type: number
          format: float
          description: Cumulative probability threshold for nucleus sampling
        min_p:
          type: number
          format: float
          description: Minimum probability threshold for token selection
        stop:
          oneOf:
            - type: string
            - type: array
              items:
                type: string
          description: Stop sequences that will halt generation
        num_ctx:
          type: integer
          description: Context length size (number of tokens)
        num_predict:
          type: integer
          description: Maximum number of tokens to generate
      additionalProperties: true
    Logprob:
      type: object
      description: Log probability information for a generated token
      properties:
        token:
          type: string
          description: The text representation of the token
        logprob:
          type: number
          description: The log probability of this token
        bytes:
          type: array
          items:
            type: integer
          description: The raw byte representation of the token
        top_logprobs:
          type: array
          items:
            $ref: '#/components/schemas/TokenLogprob'
          description: Most likely tokens and their log probabilities at this position
    TokenLogprob:
      type: object
      description: Log probability information for a single token alternative
      properties:
        token:
          type: string
          description: The text representation of the token
        logprob:
          type: number
          description: The log probability of this token
        bytes:
          type: array
          items:
            type: integer
          description: The raw byte representation of the token

````

---

# Streaming

Streaming allows you to render text as it is produced by the model.

Streaming is enabled by default through the REST API, but disabled by default in the SDKs.

To enable streaming in the SDKs, set the `stream` parameter to `True`.

## Key streaming concepts

1. Chatting: Stream partial assistant messages. Each chunk includes the `content` so you can render messages as they arrive.
2. Thinking: Thinking-capable models emit a `thinking` field alongside regular content in each chunk. Detect this field in streaming chunks to show or hide reasoning traces before the final answer arrives.
3. Tool calling: Watch for streamed `tool_calls` in each chunk, execute the requested tool, and append tool outputs back into the conversation.

## Handling streamed chunks

<Note> It is necessary to accumulate the partial fields in order to maintain the history of the conversation. This is particularly important for tool calling where the thinking, tool call from the model, and the executed tool result must be passed back to the model in the next request. </Note>

<Tabs>
  <Tab title="Python">
    ```python theme={"system"}
    from ollama import chat

    stream = chat(
      model='qwen3',
      messages=[{'role': 'user', 'content': 'What is 17 × 23?'}],
      stream=True,
    )

    in_thinking = False
    content = ''
    thinking = ''
    for chunk in stream:
      if chunk.message.thinking:
        if not in_thinking:
          in_thinking = True
          print('Thinking:\n', end='', flush=True)
        print(chunk.message.thinking, end='', flush=True)
        # accumulate the partial thinking 
        thinking += chunk.message.thinking
      elif chunk.message.content:
        if in_thinking:
          in_thinking = False
          print('\n\nAnswer:\n', end='', flush=True)
        print(chunk.message.content, end='', flush=True)
        # accumulate the partial content
        content += chunk.message.content

      # append the accumulated fields to the messages for the next request
      new_messages = [{ role: 'assistant', thinking: thinking, content: content }]
    ```
  </Tab>

  <Tab title="JavaScript">
    ```javascript theme={"system"}
    import ollama from 'ollama'

    async function main() {
      const stream = await ollama.chat({
        model: 'qwen3',
        messages: [{ role: 'user', content: 'What is 17 × 23?' }],
        stream: true,
      })

      let inThinking = false
      let content = ''
      let thinking = ''

      for await (const chunk of stream) {
        if (chunk.message.thinking) {
          if (!inThinking) {
            inThinking = true
            process.stdout.write('Thinking:\n')
          }
          process.stdout.write(chunk.message.thinking)
          // accumulate the partial thinking
          thinking += chunk.message.thinking
        } else if (chunk.message.content) {
          if (inThinking) {
            inThinking = false
            process.stdout.write('\n\nAnswer:\n')
          }
          process.stdout.write(chunk.message.content)
          // accumulate the partial content
          content += chunk.message.content
        }
      }

      // append the accumulated fields to the messages for the next request
      new_messages = [{ role: 'assistant', thinking: thinking, content: content }]
    }

    main().catch(console.error)
    ```
  </Tab>
</Tabs>

---

# Tool calling

Ollama supports tool calling (also known as function calling) which allows a model to invoke tools and incorporate their results into its replies.

## Calling a single tool

Invoke a single tool and include its response in a follow-up request.

Also known as "single-shot" tool calling.

<Tabs>
  <Tab title="cURL">
    ```shell theme={"system"}
    curl -s http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{
      "model": "qwen3",
      "messages": [{"role": "user", "content": "What is the temperature in New York?"}],
      "stream": false,
      "tools": [
        {
          "type": "function",
          "function": {
            "name": "get_temperature",
            "description": "Get the current temperature for a city",
            "parameters": {
              "type": "object",
              "required": ["city"],
              "properties": {
                "city": {"type": "string", "description": "The name of the city"}
              }
            }
          }
        }
      ]
    }'
    ```

    **Generate a response with a single tool result**

    ```shell theme={"system"}
    curl -s http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{
      "model": "qwen3",
      "messages": [
        {"role": "user", "content": "What is the temperature in New York?"},
        {
          "role": "assistant",
          "tool_calls": [
            {
              "type": "function",
              "function": {
                "index": 0,
                "name": "get_temperature",
                "arguments": {"city": "New York"}
              }
            }
          ]
        },
        {"role": "tool", "tool_name": "get_temperature", "content": "22°C"}
      ],
      "stream": false
    }'
    ```
  </Tab>

  <Tab title="Python">
    Install the Ollama Python SDK:

    ```bash theme={"system"}
    # with pip
    pip install ollama -U

    # with uv
    uv add ollama    
    ```

    ```python theme={"system"}
    from ollama import chat

    def get_temperature(city: str) -> str:
      """Get the current temperature for a city
      
      Args:
        city: The name of the city

      Returns:
        The current temperature for the city
      """
      temperatures = {
        "New York": "22°C",
        "London": "15°C",
        "Tokyo": "18°C",
      }
      return temperatures.get(city, "Unknown")

    messages = [{"role": "user", "content": "What is the temperature in New York?"}]

    # pass functions directly as tools in the tools list or as a JSON schema
    response = chat(model="qwen3", messages=messages, tools=[get_temperature], think=True)

    messages.append(response.message)
    if response.message.tool_calls:
      # only recommended for models which only return a single tool call
      call = response.message.tool_calls[0]
      result = get_temperature(**call.function.arguments)
      # add the tool result to the messages
      messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})

      final_response = chat(model="qwen3", messages=messages, tools=[get_temperature], think=True)
      print(final_response.message.content)
    ```
  </Tab>

  <Tab title="JavaScript">
    Install the Ollama JavaScript library:

    ```bash theme={"system"}
    # with npm
    npm i ollama

    # with bun
    bun i ollama
    ```

    ```typescript theme={"system"}
    import ollama from 'ollama'

    function getTemperature(city: string): string {
      const temperatures: Record<string, string> = {
        'New York': '22°C',
        'London': '15°C',
        'Tokyo': '18°C',
      }
      return temperatures[city] ?? 'Unknown'
    }

    const tools = [
      {
        type: 'function',
        function: {
          name: 'get_temperature',
          description: 'Get the current temperature for a city',
          parameters: {
            type: 'object',
            required: ['city'],
            properties: {
              city: { type: 'string', description: 'The name of the city' },
            },
          },
        },
      },
    ]

    const messages = [{ role: 'user', content: "What is the temperature in New York?" }]

    const response = await ollama.chat({
      model: 'qwen3',
      messages,
      tools,
      think: true,
    })

    messages.push(response.message)
    if (response.message.tool_calls?.length) {
      // only recommended for models which only return a single tool call
      const call = response.message.tool_calls[0]
      const args = call.function.arguments as { city: string }
      const result = getTemperature(args.city)
      // add the tool result to the messages
      messages.push({ role: 'tool', tool_name: call.function.name, content: result })

      // generate the final response
      const finalResponse = await ollama.chat({ model: 'qwen3', messages, tools, think: true })
      console.log(finalResponse.message.content)
    }
    ```
  </Tab>
</Tabs>

## Parallel tool calling

<Tabs>
  <Tab title="cURL">
    Request multiple tool calls in parallel, then send all tool responses back to the model.

    ```shell theme={"system"}
    curl -s http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{
      "model": "qwen3",
      "messages": [{"role": "user", "content": "What are the current weather conditions and temperature in New York and London?"}],
      "stream": false,
      "tools": [
        {
          "type": "function",
          "function": {
            "name": "get_temperature",
            "description": "Get the current temperature for a city",
            "parameters": {
              "type": "object",
              "required": ["city"],
              "properties": {
                "city": {"type": "string", "description": "The name of the city"}
              }
            }
          }
        },
        {
          "type": "function",
          "function": {
            "name": "get_conditions",
            "description": "Get the current weather conditions for a city",
            "parameters": {
              "type": "object",
              "required": ["city"],
              "properties": {
                "city": {"type": "string", "description": "The name of the city"}
              }
            }
          }
        }
      ]
    }'
    ```

    **Generate a response with multiple tool results**

    ```shell theme={"system"}
    curl -s http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{
      "model": "qwen3",
      "messages": [
        {"role": "user", "content": "What are the current weather conditions and temperature in New York and London?"},
        {
          "role": "assistant",
          "tool_calls": [
            {
              "type": "function",
              "function": {
                "index": 0,
                "name": "get_temperature",
                "arguments": {"city": "New York"}
              }
            },
            {
              "type": "function",
              "function": {
                "index": 1,
                "name": "get_conditions",
                "arguments": {"city": "New York"}
              }
            },
            {
              "type": "function",
              "function": {
                "index": 2,
                "name": "get_temperature",
                "arguments": {"city": "London"}
              }
            },
            {
              "type": "function",
              "function": {
                "index": 3,
                "name": "get_conditions",
                "arguments": {"city": "London"}
              }
            }
          ]
        },
        {"role": "tool", "tool_name": "get_temperature", "content": "22°C"},
        {"role": "tool", "tool_name": "get_conditions", "content": "Partly cloudy"},
        {"role": "tool", "tool_name": "get_temperature", "content": "15°C"},
        {"role": "tool", "tool_name": "get_conditions", "content": "Rainy"}
      ],
      "stream": false
    }'
    ```
  </Tab>

  <Tab title="Python">
    ```python theme={"system"}
    from ollama import chat

    def get_temperature(city: str) -> str:
      """Get the current temperature for a city
      
      Args:
        city: The name of the city

      Returns:
        The current temperature for the city
      """
      temperatures = {
        "New York": "22°C",
        "London": "15°C",
        "Tokyo": "18°C"
      }
      return temperatures.get(city, "Unknown")

    def get_conditions(city: str) -> str:
      """Get the current weather conditions for a city
      
      Args:
        city: The name of the city

      Returns:
        The current weather conditions for the city
      """
      conditions = {
        "New York": "Partly cloudy",
        "London": "Rainy",
        "Tokyo": "Sunny"
      }
      return conditions.get(city, "Unknown")


    messages = [{'role': 'user', 'content': 'What are the current weather conditions and temperature in New York and London?'}]

    # The python client automatically parses functions as a tool schema so we can pass them directly
    # Schemas can be passed directly in the tools list as well 
    response = chat(model='qwen3', messages=messages, tools=[get_temperature, get_conditions], think=True)

    # add the assistant message to the messages
    messages.append(response.message)
    if response.message.tool_calls:
      # process each tool call 
      for call in response.message.tool_calls:
        # execute the appropriate tool
        if call.function.name == 'get_temperature':
          result = get_temperature(**call.function.arguments)
        elif call.function.name == 'get_conditions':
          result = get_conditions(**call.function.arguments)
        else:
          result = 'Unknown tool'
        # add the tool result to the messages
        messages.append({'role': 'tool',  'tool_name': call.function.name, 'content': str(result)})

      # generate the final response
      final_response = chat(model='qwen3', messages=messages, tools=[get_temperature, get_conditions], think=True)
      print(final_response.message.content)
    ```
  </Tab>

  <Tab title="JavaScript">
    ```typescript theme={"system"}
    import ollama from 'ollama'

    function getTemperature(city: string): string {
      const temperatures: { [key: string]: string } = {
        "New York": "22°C",
        "London": "15°C",
        "Tokyo": "18°C"
      }
      return temperatures[city] || "Unknown"
    }

    function getConditions(city: string): string {
      const conditions: { [key: string]: string } = {
        "New York": "Partly cloudy",
        "London": "Rainy",
        "Tokyo": "Sunny"
      }
      return conditions[city] || "Unknown"
    }

    const tools = [
      {
        type: 'function',
        function: {
          name: 'get_temperature',
          description: 'Get the current temperature for a city',
          parameters: {
            type: 'object',
            required: ['city'],
            properties: {
              city: { type: 'string', description: 'The name of the city' },
            },
          },
        },
      },
      {
        type: 'function',
        function: {
          name: 'get_conditions',
          description: 'Get the current weather conditions for a city',
          parameters: {
            type: 'object',
            required: ['city'],
            properties: {
              city: { type: 'string', description: 'The name of the city' },
            },
          },
        },
      }
    ]

    const messages = [{ role: 'user', content: 'What are the current weather conditions and temperature in New York and London?' }]

    const response = await ollama.chat({
      model: 'qwen3',
      messages,
      tools,
      think: true
    })

    // add the assistant message to the messages
    messages.push(response.message)
    if (response.message.tool_calls) {
      // process each tool call 
      for (const call of response.message.tool_calls) {
        // execute the appropriate tool
        let result: string
        if (call.function.name === 'get_temperature') {
          const args = call.function.arguments as { city: string }
          result = getTemperature(args.city)
        } else if (call.function.name === 'get_conditions') {
          const args = call.function.arguments as { city: string }
          result = getConditions(args.city)
        } else {
          result = 'Unknown tool'
        }
        // add the tool result to the messages
        messages.push({ role: 'tool', tool_name: call.function.name, content: result })
      }

      // generate the final response
      const finalResponse = await ollama.chat({ model: 'qwen3', messages, tools, think: true })
      console.log(finalResponse.message.content)
    }
    ```
  </Tab>
</Tabs>

## Multi-turn tool calling (Agent loop)

An agent loop allows the model to decide when to invoke tools and incorporate their results into its replies.

It also might help to tell the model that it is in a loop and can make multiple tool calls.

<Tabs>
  <Tab title="Python">
    ```python theme={"system"}
    from ollama import chat, ChatResponse


    def add(a: int, b: int) -> int:
      """Add two numbers"""
      """
      Args:
        a: The first number
        b: The second number

      Returns:
        The sum of the two numbers
      """
      return a + b


    def multiply(a: int, b: int) -> int:
      """Multiply two numbers"""
      """
      Args:
        a: The first number
        b: The second number

      Returns:
        The product of the two numbers
      """
      return a * b


    available_functions = {
      'add': add,
      'multiply': multiply,
    }

    messages = [{'role': 'user', 'content': 'What is (11434+12341)*412?'}]
    while True:
        response: ChatResponse = chat(
            model='qwen3',
            messages=messages,
            tools=[add, multiply],
            think=True,
        )
        messages.append(response.message)
        print("Thinking: ", response.message.thinking)
        print("Content: ", response.message.content)
        if response.message.tool_calls:
            for tc in response.message.tool_calls:
                if tc.function.name in available_functions:
                    print(f"Calling {tc.function.name} with arguments {tc.function.arguments}")
                    result = available_functions[tc.function.name](**tc.function.arguments)
                    print(f"Result: {result}")
                    # add the tool result to the messages
                    messages.append({'role': 'tool', 'tool_name': tc.function.name, 'content': str(result)})
        else:
            # end the loop when there are no more tool calls
            break
      # continue the loop with the updated messages
    ```
  </Tab>

  <Tab title="JavaScript">
    ```typescript theme={"system"}
    import ollama from 'ollama'

    type ToolName = 'add' | 'multiply'

    function add(a: number, b: number): number {
      return a + b
    }

    function multiply(a: number, b: number): number {
      return a * b
    }

    const availableFunctions: Record<ToolName, (a: number, b: number) => number> = {
      add,
      multiply,
    }

    const tools = [
      {
        type: 'function',
        function: {
          name: 'add',
          description: 'Add two numbers',
          parameters: {
            type: 'object',
            required: ['a', 'b'],
            properties: {
              a: { type: 'integer', description: 'The first number' },
              b: { type: 'integer', description: 'The second number' },
            },
          },
        },
      },
      {
        type: 'function',
        function: {
          name: 'multiply',
          description: 'Multiply two numbers',
          parameters: {
            type: 'object',
            required: ['a', 'b'],
            properties: {
              a: { type: 'integer', description: 'The first number' },
              b: { type: 'integer', description: 'The second number' },
            },
          },
        },
      },
    ]

    async function agentLoop() {
      const messages = [{ role: 'user', content: 'What is (11434+12341)*412?' }]

      while (true) {
        const response = await ollama.chat({
          model: 'qwen3',
          messages,
          tools,
          think: true,
        })

        messages.push(response.message)
        console.log('Thinking:', response.message.thinking)
        console.log('Content:', response.message.content)

        const toolCalls = response.message.tool_calls ?? []
        if (toolCalls.length) {
          for (const call of toolCalls) {
            const fn = availableFunctions[call.function.name as ToolName]
            if (!fn) {
              continue
            }

            const args = call.function.arguments as { a: number; b: number }
            console.log(`Calling ${call.function.name} with arguments`, args)
            const result = fn(args.a, args.b)
            console.log(`Result: ${result}`)
            messages.push({ role: 'tool', tool_name: call.function.name, content: String(result) })
          }
        } else {
          break
        }
      }
    }

    agentLoop().catch(console.error)
    ```
  </Tab>
</Tabs>

## Tool calling with streaming

When streaming, gather every chunk of `thinking`, `content`, and `tool_calls`, then return those fields together with any tool results in the follow-up request.

<Tabs>
  <Tab title="Python">
    ```python theme={"system"}
    from ollama import chat 


    def get_temperature(city: str) -> str:
      """Get the current temperature for a city
      
      Args:
        city: The name of the city

      Returns:
        The current temperature for the city
      """
      temperatures = {
        'New York': '22°C',
        'London': '15°C',
      }
      return temperatures.get(city, 'Unknown')


    messages = [{'role': 'user', 'content': "What is the temperature in New York?"}]

    while True:
      stream = chat(
        model='qwen3',
        messages=messages,
        tools=[get_temperature],
        stream=True,
        think=True,
      )

      thinking = ''
      content = ''
      tool_calls = []

      done_thinking = False
      # accumulate the partial fields
      for chunk in stream:
        if chunk.message.thinking:
          thinking += chunk.message.thinking
          print(chunk.message.thinking, end='', flush=True)
        if chunk.message.content:
          if not done_thinking:
            done_thinking = True
            print('\n')
          content += chunk.message.content
          print(chunk.message.content, end='', flush=True)
        if chunk.message.tool_calls:
          tool_calls.extend(chunk.message.tool_calls)
          print(chunk.message.tool_calls)

      # append accumulated fields to the messages
      if thinking or content or tool_calls:
        messages.append({'role': 'assistant', 'thinking': thinking, 'content': content, 'tool_calls': tool_calls})

      if not tool_calls:
        break

      for call in tool_calls:
        if call.function.name == 'get_temperature':
          result = get_temperature(**call.function.arguments)
        else:
          result = 'Unknown tool'
        messages.append({'role': 'tool', 'tool_name': call.function.name, 'content': result})
    ```
  </Tab>

  <Tab title="JavaScript">
    ```typescript theme={"system"}
    import ollama from 'ollama'

    function getTemperature(city: string): string {
      const temperatures: Record<string, string> = {
        'New York': '22°C',
        'London': '15°C',
      }
      return temperatures[city] ?? 'Unknown'
    }

    const getTemperatureTool = {
      type: 'function',
      function: {
        name: 'get_temperature',
        description: 'Get the current temperature for a city',
        parameters: {
          type: 'object',
          required: ['city'],
          properties: {
            city: { type: 'string', description: 'The name of the city' },
          },
        },
      },
    }

    async function agentLoop() {
      const messages = [{ role: 'user', content: "What is the temperature in New York?" }]

      while (true) {
        const stream = await ollama.chat({
          model: 'qwen3',
          messages,
          tools: [getTemperatureTool],
          stream: true,
          think: true,
        })

        let thinking = ''
        let content = ''
        const toolCalls: any[] = []
        let doneThinking = false

        for await (const chunk of stream) {
          if (chunk.message.thinking) {
            thinking += chunk.message.thinking
            process.stdout.write(chunk.message.thinking)
          }
          if (chunk.message.content) {
            if (!doneThinking) {
              doneThinking = true
              process.stdout.write('\n')
            }
            content += chunk.message.content
            process.stdout.write(chunk.message.content)
          }
          if (chunk.message.tool_calls?.length) {
            toolCalls.push(...chunk.message.tool_calls)
            console.log(chunk.message.tool_calls)
          }
        }

        if (thinking || content || toolCalls.length) {
          messages.push({ role: 'assistant', thinking, content, tool_calls: toolCalls } as any)
        }

        if (!toolCalls.length) {
          break
        }

        for (const call of toolCalls) {
          if (call.function.name === 'get_temperature') {
            const args = call.function.arguments as { city: string }
            const result = getTemperature(args.city)
            messages.push({ role: 'tool', tool_name: call.function.name, content: result } )
          } else {
            messages.push({ role: 'tool', tool_name: call.function.name, content: 'Unknown tool' } )
          }
        }
      }
    }

    agentLoop().catch(console.error)
    ```
  </Tab>
</Tabs>

This loop streams the assistant response, accumulates partial fields, passes them back together, and appends the tool results so the model can complete its answer.

## Using functions as tools with Ollama Python SDK

The Python SDK automatically parses functions as a tool schema so we can pass them directly.
Schemas can still be passed if needed.

```python theme={"system"}
from ollama import chat

def get_temperature(city: str) -> str:
  """Get the current temperature for a city
  
  Args:
    city: The name of the city

  Returns:
    The current temperature for the city
  """
  temperatures = {
    'New York': '22°C',
    'London': '15°C',
  }
  return temperatures.get(city, 'Unknown')

available_functions = {
  'get_temperature': get_temperature,
}
# directly pass the function as part of the tools list
response = chat(model='qwen3', messages=messages, tools=available_functions.values(), think=True)
```

---

# Structured Outputs

<Note>
  Ollama's Cloud currently does not support structured outputs.
</Note>

Structured outputs let you enforce a JSON schema on model responses so you can reliably extract structured data, describe images, or keep every reply consistent.

## Generating structured JSON

<Tabs>
  <Tab title="cURL">
    ```shell theme={"system"}
    curl -X POST http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{
      "model": "gpt-oss",
      "messages": [{"role": "user", "content": "Tell me about Canada in one line"}],
      "stream": false,
      "format": "json"
    }'
    ```
  </Tab>

  <Tab title="Python">
    ```python theme={"system"}
    from ollama import chat

    response = chat(
      model='gpt-oss',
      messages=[{'role': 'user', 'content': 'Tell me about Canada.'}],
      format='json'
    )
    print(response.message.content)
    ```
  </Tab>

  <Tab title="JavaScript">
    ```javascript theme={"system"}
    import ollama from 'ollama'

    const response = await ollama.chat({
      model: 'gpt-oss',
      messages: [{ role: 'user', content: 'Tell me about Canada.' }],
      format: 'json'
    })
    console.log(response.message.content)
    ```
  </Tab>
</Tabs>

## Generating structured JSON with a schema

Provide a JSON schema to the `format` field.

<Note>
  It is ideal to also pass the JSON schema as a string in the prompt to ground the model's response.
</Note>

<Tabs>
  <Tab title="cURL">
    ```shell theme={"system"}
    curl -X POST http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{
      "model": "gpt-oss",
      "messages": [{"role": "user", "content": "Tell me about Canada."}],
      "stream": false,
      "format": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "capital": {"type": "string"},
          "languages": {
            "type": "array",
            "items": {"type": "string"}
          }
        },
        "required": ["name", "capital", "languages"]
      }
    }'
    ```
  </Tab>

  <Tab title="Python">
    Use Pydantic models and pass `model_json_schema()` to `format`, then validate the response:

    ```python theme={"system"}
    from ollama import chat
    from pydantic import BaseModel

    class Country(BaseModel):
      name: str
      capital: str
      languages: list[str]

    response = chat(
      model='gpt-oss',
      messages=[{'role': 'user', 'content': 'Tell me about Canada.'}],
      format=Country.model_json_schema(),
    )

    country = Country.model_validate_json(response.message.content)
    print(country)
    ```
  </Tab>

  <Tab title="JavaScript">
    Serialize a Zod schema with `z.toJSONSchema()` and parse the structured response:

    ```javascript theme={"system"}
    import ollama from 'ollama'
    import * as z from 'zod'

    const Country = z.object({
      name: z.string(),
      capital: z.string(),
      languages: z.array(z.string()),
    })

    const response = await ollama.chat({
      model: 'gpt-oss',
      messages: [{ role: 'user', content: 'Tell me about Canada.' }],
      format: z.toJSONSchema(Country),
    })

    const country = Country.parse(JSON.parse(response.message.content))
    console.log(country)
    ```
  </Tab>
</Tabs>

## Example: Extract structured data

Define the objects you want returned and let the model populate the fields:

```python theme={"system"}
from ollama import chat
from pydantic import BaseModel

class Pet(BaseModel):
  name: str
  animal: str
  age: int
  color: str | None
  favorite_toy: str | None

class PetList(BaseModel):
  pets: list[Pet]

response = chat(
  model='gpt-oss',
  messages=[{'role': 'user', 'content': 'I have two cats named Luna and Loki...'}],
  format=PetList.model_json_schema(),
)

pets = PetList.model_validate_json(response.message.content)
print(pets)
```

## Example: Vision with structured outputs

Vision models accept the same `format` parameter, enabling deterministic descriptions of images:

```python theme={"system"}
from ollama import chat
from pydantic import BaseModel
from typing import Literal, Optional

class Object(BaseModel):
  name: str
  confidence: float
  attributes: str

class ImageDescription(BaseModel):
  summary: str
  objects: list[Object]
  scene: str
  colors: list[str]
  time_of_day: Literal['Morning', 'Afternoon', 'Evening', 'Night']
  setting: Literal['Indoor', 'Outdoor', 'Unknown']
  text_content: Optional[str] = None

response = chat(
  model='gemma4',
  messages=[{
    'role': 'user',
    'content': 'Describe this photo and list the objects you detect.',
    'images': ['path/to/image.jpg'],
  }],
  format=ImageDescription.model_json_schema(),
  options={'temperature': 0},
)

image_description = ImageDescription.model_validate_json(response.message.content)
print(image_description)
```

## Tips for reliable structured outputs

* Define schemas with Pydantic (Python) or Zod (JavaScript) so they can be reused for validation.
* Lower the temperature (e.g., set it to `0`) for more deterministic completions.
* Structured outputs work through the OpenAI-compatible API via `response_format`

---

# OpenAI compatibility

Ollama provides compatibility with parts of the [OpenAI API](https://platform.openai.com/docs/api-reference) to help connect existing applications to Ollama.

## Usage

### Simple `/v1/chat/completions` example

<CodeGroup dropdown>
  ```python basic.py theme={"system"}
  from openai import OpenAI

  client = OpenAI(
      base_url='http://localhost:11434/v1/',
      api_key='ollama',  # required but ignored
  )

  chat_completion = client.chat.completions.create(
      messages=[
          {
              'role': 'user',
              'content': 'Say this is a test',
          }
      ],
      model='gpt-oss:20b',
  )
  print(chat_completion.choices[0].message.content)
  ```

  ```javascript basic.js theme={"system"}
  import OpenAI from "openai";

  const openai = new OpenAI({
    baseURL: "http://localhost:11434/v1/",
    apiKey: "ollama", // required but ignored
  });

  const chatCompletion = await openai.chat.completions.create({
    messages: [{ role: "user", content: "Say this is a test" }],
    model: "gpt-oss:20b",
  });

  console.log(chatCompletion.choices[0].message.content);
  ```

  ```shell basic.sh theme={"system"}
  curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:20b",
    "messages": [{ "role": "user", "content": "Say this is a test" }]
  }'
  ```
</CodeGroup>

### Simple `/v1/responses` example

<CodeGroup dropdown>
  ```python responses.py theme={"system"}
  from openai import OpenAI

  client = OpenAI(
      base_url='http://localhost:11434/v1/',
      api_key='ollama',  # required but ignored
  )

  responses_result = client.responses.create(
    model='qwen3:8b',
    input='Write a short poem about the color blue',
  )
  print(responses_result.output_text)
  ```

  ```javascript responses.js theme={"system"}
  import OpenAI from "openai";

  const openai = new OpenAI({
    baseURL: "http://localhost:11434/v1/",
    apiKey: "ollama", // required but ignored
  });

  const responsesResult = await openai.responses.create({
    model: "qwen3:8b",
    input: "Write a short poem about the color blue",
  });

  console.log(responsesResult.output_text);
  ```

  ```shell responses.sh theme={"system"}
  curl -X POST http://localhost:11434/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:8b",
    "input": "Write a short poem about the color blue"
  }'
  ```
</CodeGroup>

### `/v1/chat/completions` with vision example

<CodeGroup dropdown>
  ```python vision.py theme={"system"}
  from openai import OpenAI

  client = OpenAI(
      base_url='http://localhost:11434/v1/',
      api_key='ollama',  # required but ignored
  )

  response = client.chat.completions.create(
      model='qwen3-vl:8b',
      messages=[
          {
              'role': 'user',
              'content': [
                  {'type': 'text', 'text': "What's in this image?"},
                  {
                      'type': 'image_url',
                      'image_url': 'data:image/png;base64,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',
                  },
              ],
          }
      ],
      max_tokens=300,
  )
  print(response.choices[0].message.content)
  ```

  ```javascript vision.js theme={"system"}
  import OpenAI from "openai";

  const openai = new OpenAI({
    baseURL: "http://localhost:11434/v1/",
    apiKey: "ollama", // required but ignored
  });

  const response = await openai.chat.completions.create({
    model: "qwen3-vl:8b",
    messages: [
      {
        role: "user",
        content: [
          { type: "text", text: "What's in this image?" },
          {
            type: "image_url",
            image_url:
              "data:image/png;base64,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",
          },
        ],
      },
    ],
  });
  console.log(response.choices[0].message.content);
  ```

  ```shell vision.sh theme={"system"}
  curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-vl:8b",
    "messages": [{ "role": "user", "content": [{"type": "text", "text": "What is this an image of?"}, {"type": "image_url", "image_url": "data:image/png;base64,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"}]}]
  }'
  ```
</CodeGroup>

## Endpoints

### `/v1/chat/completions`

#### Supported features

* [x] Chat completions
* [x] Streaming
* [x] JSON mode
* [x] Reproducible outputs
* [x] Vision
* [x] Tools
* [x] Reasoning/thinking control (for thinking models)
* [ ] Logprobs

#### Supported request fields

* [x] `model`
* [x] `messages`
  * [x] Text `content`
  * [x] Image `content`
    * [x] Base64 encoded image
    * [ ] Image URL
  * [x] Array of `content` parts
* [x] `frequency_penalty`
* [x] `presence_penalty`
* [x] `response_format`
* [x] `seed`
* [x] `stop`
* [x] `stream`
* [x] `stream_options`
  * [x] `include_usage`
* [x] `temperature`
* [x] `top_p`
* [x] `max_tokens`
* [x] `tools`
* [x] `reasoning_effort` (`"high"`, `"medium"`, `"low"`, `"max"`, `"none"`)
* [x] `reasoning`
  * [x] `effort` (`"high"`, `"medium"`, `"low"`, `"max"`, `"none"`)
* [ ] `tool_choice`
* [ ] `logit_bias`
* [ ] `user`
* [ ] `n`

### `/v1/completions`

#### Supported features

* [x] Completions
* [x] Streaming
* [x] JSON mode
* [x] Reproducible outputs
* [ ] Logprobs

#### Supported request fields

* [x] `model`
* [x] `prompt`
* [x] `frequency_penalty`
* [x] `presence_penalty`
* [x] `seed`
* [x] `stop`
* [x] `stream`
* [x] `stream_options`
  * [x] `include_usage`
* [x] `temperature`
* [x] `top_p`
* [x] `max_tokens`
* [x] `suffix`
* [ ] `best_of`
* [ ] `echo`
* [ ] `logit_bias`
* [ ] `user`
* [ ] `n`

#### Notes

* `prompt` currently only accepts a string

### `/v1/models`

#### Notes

* `created` corresponds to when the model was last modified
* `owned_by` corresponds to the ollama username, defaulting to `"library"`

### `/v1/models/{model}`

#### Notes

* `created` corresponds to when the model was last modified
* `owned_by` corresponds to the ollama username, defaulting to `"library"`

### `/v1/embeddings`

#### Supported request fields

* [x] `model`
* [x] `input`
  * [x] string
  * [x] array of strings
  * [ ] array of tokens
  * [ ] array of token arrays
* [x] `encoding format`
* [x] `dimensions`
* [ ] `user`

### `/v1/images/generations` (experimental)

> Note: This endpoint is experimental and may change or be removed in future versions.

Generate images using image generation models.

<CodeGroup dropdown>
  ```python images.py theme={"system"}
  from openai import OpenAI

  client = OpenAI(
      base_url='http://localhost:11434/v1/',
      api_key='ollama',  # required but ignored
  )

  response = client.images.generate(
      model='x/z-image-turbo',
      prompt='A cute robot learning to paint',
      size='1024x1024',
      response_format='b64_json',
  )
  print(response.data[0].b64_json[:50] + '...')
  ```

  ```javascript images.js theme={"system"}
  import OpenAI from "openai";

  const openai = new OpenAI({
    baseURL: "http://localhost:11434/v1/",
    apiKey: "ollama", // required but ignored
  });

  const response = await openai.images.generate({
    model: "x/z-image-turbo",
    prompt: "A cute robot learning to paint",
    size: "1024x1024",
    response_format: "b64_json",
  });

  console.log(response.data[0].b64_json.slice(0, 50) + "...");
  ```

  ```shell images.sh theme={"system"}
  curl -X POST http://localhost:11434/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "model": "x/z-image-turbo",
    "prompt": "A cute robot learning to paint",
    "size": "1024x1024",
    "response_format": "b64_json"
  }'
  ```
</CodeGroup>

#### Supported request fields

* [x] `model`
* [x] `prompt`
* [x] `size` (e.g. "1024x1024")
* [x] `response_format` (only `b64_json` supported)
* [ ] `n`
* [ ] `quality`
* [ ] `style`
* [ ] `user`

### `/v1/responses`

> Note: Added in Ollama v0.13.3

Ollama supports the [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses). Only the non-stateful flavor is supported (i.e., there is no `previous_response_id` or `conversation` support).

#### Supported features

* [x] Streaming
* [x] Tools (function calling)
* [x] Reasoning summaries (for thinking models)
* [ ] Stateful requests

#### Supported request fields

* [x] `model`
* [x] `input`
* [x] `instructions`
* [x] `tools`
* [x] `stream`
* [x] `temperature`
* [x] `top_p`
* [x] `max_output_tokens`
* [ ] `previous_response_id` (stateful v1/responses not supported)
* [ ] `conversation` (stateful v1/responses not supported)
* [ ] `truncation`

## Models

Before using a model, pull it locally `ollama pull`:

```shell theme={"system"}
ollama pull llama3.2
```

### Default model names

For tooling that relies on default OpenAI model names such as `gpt-3.5-turbo`, use `ollama cp` to copy an existing model name to a temporary name:

```shell theme={"system"}
ollama cp llama3.2 gpt-3.5-turbo
```

Afterwards, this new model name can be specified the `model` field:

```shell theme={"system"}
curl http://localhost:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": "Hello!"
            }
        ]
    }'
```

### Setting the context size

The OpenAI API does not have a way of setting the context size for a model. If you need to change the context size, create a `Modelfile` which looks like:

```
FROM <some model>
PARAMETER num_ctx <context size>
```

Use the `ollama create mymodel` command to create a new model with the updated context size. Call the API with the updated model name:

```shell theme={"system"}
curl http://localhost:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mymodel",
        "messages": [
            {
                "role": "user",
                "content": "Hello!"
            }
        ]
    }'
```
