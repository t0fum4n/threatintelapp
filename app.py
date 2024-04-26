from flask import Flask, render_template, request, jsonify
import feedparser
from bs4 import BeautifulSoup
import ollama
import requests
from keys import access_token, list_id

app = Flask(__name__)

@app.route('/create_clickup_task', methods=['POST'])
def create_clickup_task():
    article = request.json
    title = article['title']
    description = article['description']
    content = f"{description}\n\nOverview and Mitigation Steps:\n{article['mitigation']}"

    clickup_url = f"https://api.clickup.com/api/v2/list/{list_id}/task"  # Use the list_id from keys.py
    headers = {
        'Authorization': access_token,  # Use the API key from keys.py
        'Content-Type': 'application/json',
    }
    data = {
        "name": title,
        "description": content
    }
    response = requests.post(clickup_url, headers=headers, json=data)
    if response.status_code == 200:
        return jsonify({'status': 'Task created successfully'})
    else:
        return jsonify({'status': 'Failed to create task', 'error': response.text}), response.status_code

@app.route('/llama_mitigation', methods=['POST'])
def llama_mitigation():
    content = request.json['description']
    try:
        response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': "Provide an overview and mitigation steps for: " + content}])
        return jsonify({'mitigation': response['message']['content']})
    except ollama.ResponseError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    keyword = request.args.get('keyword', '').lower()
    feed_url = 'https://feeds.feedburner.com/TheHackersNews'
    feed = feedparser.parse(feed_url)
    articles = [
        {'title': entry.title, 'description': entry.summary, 'link': entry.link}
        for entry in feed.entries
        if keyword in entry.title.lower() or keyword in entry.summary.lower()
    ]
    return render_template('index.html', articles=articles)


@app.route('/llama_response', methods=['POST'])
def llama_response():
    article_url = request.json['url']
    try:
        # Fetch the content of the article
        response = requests.get(article_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Assuming that the article body is within <p> tags
        article_content = soup.find_all('p')
        full_text = ' '.join([para.get_text() for para in article_content])

        # Adding a specific prompt to the content
        prompt = "Give a brief summary of this article: " + full_text

        #print("Sending to LLM:", prompt)  # Log the content being sent to the LLM

        # Send the prompt and the text to the LLM
        llm_response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
        return jsonify({'llama_response': llm_response['message']['content']})
    except ollama.ResponseError as e:
        return jsonify({'llama_response': f"Error getting response: {e}"}), 500
    except Exception as e:
        return jsonify({'llama_response': f"Error processing the article: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
