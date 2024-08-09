import simpy
import os
import random
import statistics
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, send_from_directory, send_file

app = Flask(__name__)

class Bookshop:
    def __init__(self, env, num_servers, service_time):
        self.env = env
        self.server = simpy.Resource(env, num_servers)
        self.service_time = service_time
        self.customers = []

    def serve_customer(self, customer):
        """Serve a customer."""
        arrival_time = self.env.now

        with self.server.request() as request:
            yield request
            start_service = self.env.now
            yield self.env.timeout(random.expovariate(1.0 / self.service_time))
            end_service = self.env.now

            waiting_time = start_service - arrival_time
            service_time = end_service - start_service

            self.customers.append({
                'customer': customer,
                'arrival_time': arrival_time,
                'start_service': start_service,
                'end_service': end_service,
                'waiting_time': waiting_time,
                'service_time': service_time
            })

def setup(env, num_customers, inter_arrival_time, bookshop):
    """Generate new customers at random intervals."""
    for i in range(num_customers):
        yield env.timeout(random.expovariate(1.0 / inter_arrival_time))
        env.process(bookshop.serve_customer(f'Customer {i+1}'))

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    RANDOM_SEED = data['RANDOM_SEED']
    NEW_CUSTOMERS = data['NEW_CUSTOMERS']
    INTER_ARRIVAL_TIME = data['INTER_ARRIVAL_TIME']
    SERVICE_TIME = data['SERVICE_TIME']
    NUM_SERVERS = data['NUM_SERVERS']

    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    bookshop = Bookshop(env, NUM_SERVERS, SERVICE_TIME)
    env.process(setup(env, NEW_CUSTOMERS, INTER_ARRIVAL_TIME, bookshop))
    env.run()

    average_wait_time = statistics.mean([customer['waiting_time'] for customer in bookshop.customers]) if bookshop.customers else 0

    # Generate and save the graph
    plt.figure(figsize=(10, 6))
    wait_times = [customer['waiting_time'] for customer in bookshop.customers]
    service_times = [customer['service_time'] for customer in bookshop.customers]
    plt.plot(wait_times, label='Wait Time', marker='o')
    plt.plot(service_times, label='Service Time', marker='x')
    plt.xlabel('Customer')
    plt.ylabel('Time (minutes)')
    plt.title('Customer Wait and Service Times')
    plt.legend()
    plt.grid(True)
    plt.savefig('static/simulation_graph.png')
    plt.close()

    return jsonify({
        'average_wait_time': average_wait_time,
        'customers': bookshop.customers
    })

@app.route('/graph')
def graph():
    return send_from_directory('static', 'simulation_graph.png')

@app.route('/')
def index():
    return send_from_directory('', 'index.html')

@app.route('/styles.css')
def styles():
    return send_file('', 'styles.css')

# if __name__ == '__main__':
#     app.run(debug=True)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
