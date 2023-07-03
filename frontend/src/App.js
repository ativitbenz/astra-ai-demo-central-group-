import { Configuration, OpenAIApi } from 'openai';

import FormSection from './components/FormSection';
import AnswerSection from './components/AnswerSection';

import { useState } from 'react';

import axios from 'axios';


const App = () => {

	const [storedValues, setStoredValues] = useState([]);
	const [products, setProducts] = useState([]);

	const ProductCard = ({ product }) => {
		return (
		  <div className="card">
			<tbody>
				{product.map((product, index) => (
				<tr key={index}>
					<td>{product.id}</td>
					<td>{product.name}</td>
					<td>{product.price}</td>
					<td>{product.description}</td>
				</tr>
				))}
			</tbody>
		  </div>
		);
	  };
	

	const generateResponse = async (newQuestion, setNewQuestion) => {

		try {
			const response = await axios.post('http://localhost:9000/similaritems', { newQuestion });
			if (response.data.botresponse) {
				setStoredValues([
					{
						question: newQuestion,
						answer: response.data.botresponse,
					},
					...storedValues,
				]);
				setNewQuestion('');	
			}

			setProducts(response.data.products);
			
		  } catch (error) {
			console.error(error);
		  }

		
	};

	return (
		<div>
			<div className="header-section">
				<h1 style={{ fontSize: 18 }}>Generative AI Retail Product Recommendations demo powered by Astra VectorDB</h1>
				{storedValues.length < 1 && (
					<p>
						Please type what you looking for
					</p>
				)}
			</div>

			<FormSection generateResponse={generateResponse} />

			{storedValues.length > 0 && <AnswerSection storedValues={storedValues} />}

			<ProductCard product={products} />

		

		</div>
	);
};

export default App;