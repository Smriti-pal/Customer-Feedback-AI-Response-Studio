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



## How to Run

Follow the steps below to run the project locally.

### 1. Clone the Repository

Clone the GitHub repository:

```bash
git clone https://github.com/Smriti-pal/Customer-Feedback-AI-Response-Studio.git
```

Navigate to the project folder:

```bash
cd Customer-Feedback-AI-Response-Studio
```

You can also download the repository as a ZIP file and extract it.

### 2. Check the Dataset

Make sure `Reviews.csv` is present in the project folder.

### 3. Install Required Libraries

Open Command Prompt, Anaconda Prompt, or Terminal and run:

```bash
pip install -U pandas google-genai jupyter
```

### 4. Open Jupyter Notebook

Start Jupyter Notebook:

```bash
jupyter notebook
```

Open the project notebook from the Jupyter interface.

### 5. Run the Notebook

Run all the notebook cells **from top to bottom**.

The notebook will:

* Load and clean the customer reviews.
* Identify critical negative reviews.
* Analyze complaint-related keywords.
* Select the top 3 critical reviews.
* Generate personalized apology emails using Google Gemini.

### 6. Generate AI Responses

The notebook will use the configured **Google Gemini API key** to generate personalized apology emails for the three selected critical reviews.

### 7. View the Results

After successful execution, the notebook will display:

* Cleaned customer review data
* Critical negative reviews
* Complaint keyword analysis
* Top 3 selected critical reviews
* Personalized AI-generated apology emails



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

