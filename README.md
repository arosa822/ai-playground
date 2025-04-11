# Flask LLM File Upload Application

This is a simple Flask application that provides an endpoint to upload a file and process it using a language model (LLM). The application uses the `transformers` library to load and interact with the LLM.

## Features

- Upload a text file via a POST request.
- Process the file content using a pre-trained language model.
- Return the model's response as JSON.

## Setup

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install the required packages:**

   Ensure you have Python 3.7+ installed. Then, install the dependencies:

   ```bash
   pip install flask transformers torch
   ```

3. **Run the application:**

   ```bash
   FLASK_APP=app.py flask run
   ```

   The application will start on `http://localhost:5000`.

## Usage

- **Health check:**

  Example using `curl`:
  ```bash
  curl -X GET http://localhost:5000/health
  ```


- **upload a file:**

  Send a POST request to the `/upload` endpoint with a file. You can use tools like `curl` or Postman for testing.

  Example using `curl`:

  ```bash
  curl -X POST -F 'file=@path/to/your/file.txt' http://localhost:5000/upload
  ```

  The response will be a JSON object containing the model's output.

## License

This project is licensed under the MIT License.
