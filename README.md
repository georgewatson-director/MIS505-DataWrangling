# MIS505-DataWrangling

The instructions for this final course assignment in CSU Global's MIS 505, Data Wrangling, begin with:
"In a given country, did the enrollment in primary education increase with the improvement of per capita GDP in the past 20 years? As a data wrangling expert, your job will be to acquire and provide a clean dataset that contains educational enrollment and GDP data side by side for a country of your choice. Note: You may choose any country except for the one covered in your textbook (India)."

The tables in this repository ate output tables in the format required by the assignment. all have the same format, each containing the same data for different countries.

The format is described in JSON in the TableDescriptor.json file.

The paper I submitted explaining the research project and its results is included in this repo, file name: 
	Watson - MIS505 Portfolio Project.pdf

The code file, PortfolioProject.py, is the code run to produce all of the database and csv files in this repo.

The source data which PortfolioProject.py uses to produce its output was downloaded using the following links, ones which CSU Global provided for this purpose.  CSU Global extracted the contents of these files from the bulk data which can be downloaded at the World Bank Group's open data bulk download page.

	WDI_csv.zip:	https://csuglobal.instructure.com/courses/120813/files/9754905?wrap=1
	API_SE.PRM.ENRL_DS2_en_csv_v2_4538564-1.zip:
			https://csuglobal.instructure.com/courses/120813/files/9754904?wrap=1

pandas_gui_app.py is a PyQt5 GUI front end for the Pandas DataFrame.  You can load and explore CSV files as Pandas DataFrames with it.  Dependencies, such as PyQt5, will need to be installed before running it.
