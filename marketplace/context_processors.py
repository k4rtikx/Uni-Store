import os

def google_oauth_context(request):
    client_id = os.getenv('GOOGLE_CLIENT_ID', '').strip()
    return {
        'google_oauth_configured': bool(client_id and len(client_id) > 5 and 'your-' not in client_id),
    }
