from flask import Flask, render_template, request, jsonify
import feedparser, requests
from bs4 import BeautifulSoup
import ollama

app = Flask(__name__)


@app.route('/')
def index():
    feed_url = 'https://feeds.feedburner.com/TheHackersNews'
    feed = feedparser.parse(feed_url)
    articles = [{'title': entry.title, 'description': entry.summary, 'link': entry.link} for entry in feed.entries]
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
        llm_response = ollama.chat(model='phi3', messages=[{'role': 'user', 'content': prompt}])
        return jsonify({'llama_response': llm_response['message']['content']})
    except ollama.ResponseError as e:
        return jsonify({'llama_response': f"Error getting response: {e}"}), 500
    except Exception as e:
        return jsonify({'llama_response': f"Error processing the article: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
