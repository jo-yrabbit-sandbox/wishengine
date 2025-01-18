import json
import requests
from datetime import datetime
import logging

class MessageAPIClient():

    def __init__(self, bot_id, base_url, debug=False, logger=None):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the API server (e.g., 'http://api.example.com')
            bot_id: Unique identifier for this bot
        """
        self.base_url = base_url.rstrip('/')
        self.bot_id = bot_id
        self.debug=debug
        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger


    def generate_message(self, state='READY', text=''):
        return {
            "bot_id": self.bot_id,
            'message': {
                "state": state,
                "text": text,
                "timestamp": datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            }
        }

    def get_health(self, debug=False) -> dict:
        """Get health"""
        response = self._make_request(
            method='GET',
            endpoint='/health',
        )

        if self.debug:
            return json.dumps(response)
        return response.get('status', '')


    def get_messages(self, debug=False, **kwargs) -> list:
        """
        Get messages, optionally filtered by user
        
        Args:
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            List of message dictionaries
        """
        params = {
            'bot_id': self.bot_id
        }
        allowed_params = ['state', 'limit']
        for p in allowed_params:
            v = kwargs.get(p, None)
            if (v is not None) and str(v):
                params.update({p: v})
        
        response = self._make_request(
            method='GET',
            endpoint='/api/v1/messages',
            params=params
        )

        if self.debug:
            return json.dumps(response)
        return response.get('data', [])


    def store_message(self, text, state, debug=False) -> dict:
        """
        Store a new message
        
        Args:
            state: Bot state at time of storing message
            text: Message text
            
        Returns:
            Response from API server
        """
        if not text:
            error = f'Cannot store blank messages'
            self.logger.error(error)
            raise Exception(error)

        payload = self.generate_message(state=state, text=text)

        response = self._make_request(
            method='POST',
            endpoint='/api/v1/messages',
            json=payload
        )
        if self.debug:
            return json.dumps(response)
        return response.get('status', '')


    def _make_request(self, method, endpoint, **kwargs) -> dict:
        """
        Make HTTP request to API server
        
        Args:
            method: HTTP method ('GET', 'POST', etc.)
            endpoint: API endpoint (will be appended to base_url)
            **kwargs: Additional arguments to pass to requests
        
        Returns:
            Response JSON
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                # headers=self.headers,
                **kwargs
            )
            
            # Raise error for bad status codes
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error = f'API request failed: {str(e)}'
            self.logger.error(error)
            raise Exception(error)
        except ValueError as e:
            error = f'Invalid JSON response: {str(e)}'
            self.logger.error(e)
            raise Exception(e)
