@app.route('/api/stock-data', methods=['POST'])
def get_stock_data():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        # Check if API key exists
        if not FINNHUB_API_KEY:
            app.logger.error('FINNHUB_API_KEY not set in environment')
            return jsonify({'error': 'API key not configured'}), 500
        
        # Calculate date range (last 365 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Convert to Unix timestamps
        end_timestamp = int(end_date.timestamp())
        start_timestamp = int(start_date.timestamp())
        
        # Finnhub API endpoint
        url = f'https://finnhub.io/api/v1/stock/candle'
        params = {
            'symbol': symbol,
            'resolution': 'D',
            'from': start_timestamp,
            'to': end_timestamp,
            'token': FINNHUB_API_KEY
        }
        
        app.logger.info(f'Requesting data for {symbol}')
        response = requests.get(url, params=params, timeout=10)
        
        # Log the response for debugging
        app.logger.info(f'Response status: {response.status_code}')
        app.logger.info(f'Response body: {response.text}')
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for API errors
            if 'error' in result:
                app.logger.error(f'API Error: {result["error"]}')
                return jsonify({'error': f'API Error: {result["error"]}'}), 400
            
            if result.get('s') == 'no_data':
                return jsonify({'error': 'No data found for this symbol'}), 404
            
            # Format the data
            formatted_data = []
            for i in range(len(result['t'])):
                formatted_data.append({
                    'date': datetime.fromtimestamp(result['t'][i]).strftime('%Y-%m-%d'),
                    'open': round(result['o'][i], 2),
                    'high': round(result['h'][i], 2),
                    'low': round(result['l'][i], 2),
                    'close': round(result['c'][i], 2),
                    'volume': result['v'][i]
                })
            
            return jsonify({
                'symbol': symbol,
                'data': formatted_data
            })
        else:
            app.logger.error(f'HTTP Error {response.status_code}: {response.text}')
            return jsonify({'error': f'HTTP {response.status_code}: {response.text}'}), 500
            
    except requests.Timeout:
        return jsonify({'error': 'Request timeout - please try again'}), 504
    except Exception as e:
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': f'Server error: {str(e)}'}), 500