\# Customer Review Analysis and Generative AI Outreach



\## Project Objective



The objective of this project is to analyze customer reviews, identify

critical negative reviews using rule-based logic, and generate personalized

apology emails using Generative AI.



\## Data Cleaning



The dataset was loaded using Pandas.



The following cleaning steps were performed:



\- Missing values were identified.

\- Duplicate records were identified and removed.

\- Reviews with missing text were removed.

\- Review text was converted to lowercase.

\- Unnecessary special characters and extra spaces were removed.



\## Rule-Based Review Analysis



No machine learning model was used.



Reviews with a rating of 1 or 2 stars were classified as critical reviews.



Complaint-related keywords were identified using string manipulation and

keyword counting.



\## Selecting the Top 3 Reviews



The three most critical reviews were selected from the 1-star reviews.



The selection considered:



\- Negative rating severity

\- Number of complaint-related keywords

\- Review length and level of detail



\## Generative AI



Google Gemini API was used to generate personalized apology emails for

the three selected reviews.



The prompt instructed Gemini to:



\- Acknowledge the customer's specific problems.

\- Show empathy.

\- Apologize professionally.

\- Address the main complaints.

\- Avoid blaming the customer.

\- Avoid inventing refunds, replacements, compensation, or company actions.

\- Keep the email concise and professional.



\## Technologies Used



\- Python

\- Pandas

\- Collections

\- Jupyter Notebook

\- Google Gemini API



\## How to Run



1\. Place `Reviews.csv` in the same folder as the Jupyter Notebook.

2\. Open the notebook in Jupyter Notebook or JupyterLab.

3\. Install the Gemini package:



```bash

pip install -U google-genai



4\. Run the notebook cells from top to bottom.

5\. Enter the Gemini API key when prompted.

6\. Review the three generated apology emails.





**API Key Security**



The Gemini API key should not be hard-coded in the notebook or shared

publicly.



The notebook uses getpass() to enter the API key securely.





**Output**



The project produces:



* Cleaned customer review data
* Critical negative reviews
* Complaint keyword analysis
* Three selected critical reviews
* Three personalized AI-generated apology emails





**Conclusion**



This project demonstrates how data wrangling, rule-based analysis,

keyword identification, and Generative AI can be combined to identify

important customer complaints and automate personalized customer

communication.

