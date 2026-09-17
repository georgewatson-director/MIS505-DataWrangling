#   University:     Colorado State University Global
#   Course:         MIS 505 - Data Wrangling
#   Term:           26FA
#   Student:        George Keith Watson
#   Student ID:     354019
#   Assignment:     Module 8 - Portfolio Project
#   Date Due:       September 13, 2026
#
#   Workflow Documentation:
#       0. Instantiation of classes is not anticipated in this script, so for security this program
#               is written using @staticmethod's in its classes which have no __init__() method.
#               The code works as a script to be run each time a set of GDP and primary education
#               data is needed for a particular selection of countries.
#       1. When this program is started, the first routine to run is PortfolioProject.load_WDI().
#               This method, along with the next to be run, PortfolioProject.load_PRM_ENRL(),
#               loads the data provided for this assignment as downloaded CSV files. CSU Global provided
#               the data files for this assignment, WDIData.csv, which is the world development indicator
#               (WDI) data from the World Bank, and API_SE.PRM.ENRL_DS2_en_csv_v2_4538564.csv, which
#               is the primary education enrollment data for each country, data also included in the
#               WDIData.csv file under the same WDI code/identifie: SE.PRM.ENRL.
#       2. So that the data files, which are over 200 MB in size, do not need to be loaded for each
#               country the user want to extract the subject WDI from, the DataFrames constructed
#               on load are stored in class level variables in the PorforlioProject class.
#               On  particular script run, any number of countries' data can be extracted and stored
#               to the required SQLite DB and CSV files.
#       3. The next method to be run is CountryData.initializeStorage(), which produces an SQLite
#               database file named CountryIndicatorDb in the output folder, "production data",
#               Various useful data extraction and reorganizing tables are built in this DB.
#               This particular method does an integrity check to see if all of the WDI are present
#               for all countries in the database, which the data passes, and then constructs the
#               IndicatorNameMap table, which contains a simple map of the indicator codes to their
#               names.
#       4. The next method to be run is PortfolioProject.makeAssignment_8_DB_n_CSV('Argentina'), which
#               builds the output files required for this assignment, an SQLite database file and a
#               CSV file with the fields "Year", "GDP", and "Primary Enrollment". GDP is stated in
#               current U.S. Dollars, and Primary Enrollment is simply the total number of students
#               enrolled in primary education in that year.
#               The __main__ script of this program can produce any number of country specific data files
#               in a single run, loading the master data files only once, by appending calls to
#               PortfolioProject.makeAssignment_8_DB_n_CSV( CountryName ) to the end of this script.
#
#       The next step in development will be to use this program as a source of code for a general
#       API for selecting particular data concerning any country in the downloadable World Bank WDI
#       data and producing a study table in an SQLite database for the topic which the selection of WDI
#       is relevant to. Each country should have its own table in such a database for clarity of the
#       SQL used to produce reports and the Python or R used to generate viauals.
#
import math
from collections import OrderedDict
from os import environ
from sqlite3 import connect
from sys import stderr
from os.path import isdir, isfile
from datetime import datetime

import pandas
import numpy
from matplotlib import pyplot

MODULE_NAME     = "MIS_505_Portfolio_Project"
TESTING         = True
DEBUG           = False


class CountryData:

    CountryIndicatorDbFileName = "CountryIndicatorDb"
    DataFolder = environ['HOME'] + '/ACTIVITIES/Graduate School/CSU Global/Advanced Data Analytics Certificate/Courses/MIS 505 - Data Wrangling/Assignments/Week 8/production data'
    WDIDataCSVFileName = '/WDIData.csv'

    @staticmethod
    def initializeStorage():
        dbFilePath = CountryData.DataFolder + '/' + CountryData.CountryIndicatorDbFileName
        connection = connect(dbFilePath)
        connection.execute("""CREATE TABLE IF NOT EXISTS "IndicatorNameMap" (
                                "Indicator Code"	TEXT NOT NULL,
                                "Indicator Name"	TEXT NOT NULL)""")
        if PortfolioProject.WDI_DATA_FRAME is None:
            wdiDataFrame        = PortfolioProject.load_WDI()
        else:
            wdiDataFrame = PortfolioProject.WDI_DATA_FRAME
        if wdiDataFrame is None:
            return False
        #   Produce parallel data lists from columns: 'Country Name', 'Indicator Name',
        #       'Indicator Code'
        countryNames = wdiDataFrame['Country Name'].to_list()
        rowCountCountryNames = len(countryNames)
        indicatorName = wdiDataFrame['Indicator Name'].to_list()
        rowCountIndicatorName = len(indicatorName)
        indicatorCode = wdiDataFrame['Indicator Code'].to_list()
        rowCountIndicatorCode = len(indicatorCode)
        if rowCountCountryNames != rowCountIndicatorName:
            print("\nWarning: The row count for the Country Names column is not equal to the row count for the Indicator Name column", file=stderr)
        if rowCountCountryNames !=  rowCountIndicatorCode:
            print("\nWarning: The row count for the Country Name column is not equal to the row count for the Indicator Code", file=stderr)
        if rowCountIndicatorName !=  rowCountIndicatorCode:
            print("\nWarning: The row count for the Indicator Name column is not equal to the row count for the Indicator Code column", file=stderr)
        #   No warnings were printed on 2026-09-04
        #   Still assuming they are parallel regardless of warnings, use minimum length for
        #       row count:
        rowCount = min(rowCountCountryNames, rowCountIndicatorName, rowCountIndicatorCode)

        #   Data Quality Check:
        #       Check to see if all of the indicator codes present in any one country are
        #           present in all.
        #   This ran with zero warnings on 2026-09-04.
        countryNameToWDIlistMap = {}
        codeCount = 1442
        rowIdx = 0
        currentCountry = None
        sampleCodeList = None
        while rowIdx < rowCount:
            if countryNames[rowIdx] not in countryNameToWDIlistMap:
                if currentCountry is not None:
                    if sampleCodeList is None:
                        sampleCodeList = countryNameToWDIlistMap[countryNames[rowIdx-1]]
                    else:
                        if sampleCodeList != countryNameToWDIlistMap[countryNames[rowIdx-1]]:
                            print("Warning: Indicator Code lists for two countries are not the same", file=stderr)
                else:
                    currentCountry = countryNames[rowIdx]
                countryNameToWDIlistMap[countryNames[rowIdx]] = []
            if sampleCodeList is None:
                sampleCodeList
            countryNameToWDIlistMap[countryNames[rowIdx]].append(indicatorCode[rowIdx])
            rowIdx += 1
        #   Construct table mapping all of the WDI codes to their names for use in reports built
        #       using the codes as column names or row selectors, depending on the database format.
        indicatorCode = indicatorCode[:codeCount]
        indicatorName = indicatorName[:codeCount]
        rowIdx = 0
        while rowIdx < codeCount:
            connection.execute("""INSERT INTO "IndicatorNameMap" 
                                ("Indicator Code", "Indicator Name") 
                                VALUES ("{indicatorCode}", "{indicatorName}")""".
                                format(indicatorCode=indicatorCode[rowIdx],
                                       indicatorName=indicatorName[rowIdx]))
            rowIdx += 1
        connection.commit()
        connection.close()
        return True

    @staticmethod
    def getIndicatorNameMap():
        """
        Load the IndicatorNameMap table and build maps whic provide the WDI Code for any WDI Name and
        the WDI Name for any WDI Code.
        :return: nameToCodeMap, codeToNameMap
        """
        dbFilePath = CountryData.DataFolder + '/' + CountryData.CountryIndicatorDbFileName
        connection = connect(dbFilePath)
        entries = connection.execute("""SELECT * FROM IndicatorNameMap;""").fetchall()
        connection.close()

        nameToCodeMap = OrderedDict()
        codeToNameMap = OrderedDict()
        for entry in entries:
            nameToCodeMap[entry[1]] = entry[0]
            codeToNameMap[entry[0]] = entry[1]
        return nameToCodeMap, codeToNameMap


class PortfolioProject:

    DataFolder = environ['HOME'] + '/ACTIVITIES/Graduate School/CSU Global/Advanced Data Analytics Certificate/Courses/MIS 505 - Data Wrangling/Assignments/Week 8/data downloaded'
    WDI_CSVFileName = '/WDIData.csv'
    PRM_ENRL_CSVFileName = '/API_SE.PRM.ENRL_DS2_en_csv_v2_4538564.csv'

    WDI_DATA_FRAME = None
    WDI_SOURCE_DATA = None
    PRM_ENRL_DATA_FRAME = None

    @staticmethod
    def load_PRM_ENRL():
        prmEnrlDataFrame = None
        enrollmentDataFilePath =    PortfolioProject.DataFolder + PortfolioProject.PRM_ENRL_CSVFileName
        if not isfile(enrollmentDataFilePath):
            print("\nDownloaded data file does not exist:\t" + enrollmentDataFilePath, file=stderr)
        else:
            try:
                prmEnrlDataFrame = pandas.read_csv(enrollmentDataFilePath, skiprows=4, header=0)
                columnNames = prmEnrlDataFrame.columns.values.tolist()
                print("\nNames of columns in the PRM ENRL DataFrame:", columnNames)
                print('\nPrmEnrlDataFrame:\n', prmEnrlDataFrame.head(10))
            except Exception as ex:
                print("\nPandas construction of EDU DataFrame from CSV file failed with:")
                print(ex)
        PortfolioProject.PRM_ENRL_DATA_FRAME = prmEnrlDataFrame
        return prmEnrlDataFrame

    @staticmethod
    def pivotEduData(countryName: str):
        if PortfolioProject.PRM_ENRL_DATA_FRAME is None:
            eduCsvFilePath = PortfolioProject.DataFolder + PortfolioProject.PRM_ENRL_CSVFileName
            eduDataFrame = pandas.read_csv(eduCsvFilePath, skiprows=4)
        else:
            eduDataFrame = PortfolioProject.PRM_ENRL_DATA_FRAME
        #   Extract the data for the particular country
        countryDF = eduDataFrame[eduDataFrame['Country Name'] == countryName]
        if DEBUG:
            print("\ncountryDF:\n", countryDF.head(10))
        columnNames = eduDataFrame.columns.to_list()
        yearList = []
        wdiList = []
        for columnName in columnNames:
            if columnName.isnumeric():
                yearList.append(int(columnName))
                wdiValue = countryDF[columnName].values[0]
                if not math.isnan(wdiValue):
                    wdiList.append(countryDF[columnName].values[0])
                else:
                    wdiList.append(None)
        return countryDF, yearList, wdiList

    @staticmethod
    def load_WDI_Data(refresh: bool=False):
        """
        Load the data for the particular named country corresponding to the listed wdiCodes.
        :param countryName:
        :param wdiCode:
        :return:
        """
        if not PortfolioProject.WDI_SOURCE_DATA is None and not refresh:
            return PortfolioProject.WDI_SOURCE_DATA
        wdiDataFrame = None
        WDIDataCSVFilePath = PortfolioProject.DataFolder + PortfolioProject.WDI_CSVFileName
        if not isfile(WDIDataCSVFilePath):
            print("\nDownloaded data file does not exist:\t" + WDIDataCSVFilePath, file=stderr)
        else:
            try:
                startTime = datetime.now()
                wdiDataFrame = pandas.read_csv(WDIDataCSVFilePath)
                print("\nLoaded WDI CSV file into Pandas DataFrame:")
                print(wdiDataFrame.head(10))
                print("\nUnique Country Names in WDI DataFrame:", wdiDataFrame['Country Name'].unique().tolist())
            except Exception as ex:
                print("\nPandas construction of WDI DataFrame from CSV file failed with:")
                print(ex)
            finally:
                endTime = datetime.now()
                loadTime = endTime - startTime
                print("\nTime required to load 209 MB WDI CSV data file:\t", loadTime)
        columnNames = wdiDataFrame.columns.to_list()
        PortfolioProject.WDI_DATA_FRAME = wdiDataFrame

        PortfolioProject.WDI_SOURCE_DATA = {
            'columnNames': columnNames,
            'wdiDataFrame': wdiDataFrame
        }
        return PortfolioProject.WDI_SOURCE_DATA

    @staticmethod
    def makeAssignment_8_DB_n_CSV(countryName: str= "Argentina", force: bool=False):
        """
        Make a separate DB file named Assignment8_[country].sqlitedb
            with a single table in it named Assignment8_[country]
            and a separate CSV file named Assignment8_[country].csv.
        :param countryName:
        :param force:
        :return:
        """
        countryDbPath = CountryData.DataFolder + '/' + 'Assignment8_' + countryName + '.sqlitedb'
        tableName = 'Assignment8_' + countryName
        report = {}

        #   If table already exists, do not rewrite unless force==True
        connection = connect(countryDbPath)
        tableNamePresent = connection.execute("""SELECT name from sqlite_master WHERE type='table';""").fetchall()
        if len(tableNamePresent) > 0 and tableNamePresent[0][0] == tableName:
            if not force:
                report['Error'] = "Table for specified country already exists:\t" + tableName
                return report
            else:
                connection.execute("""DROP TABLE "{}";""".format(tableName))

        connection.execute("""CREATE TABLE IF NOT EXISTS "{tableName}"
                                ("Year" INTEGER NOT NULL,
                                "Primary Enrollment" NUMERIC,
                                "GDP" NUMERIC);""".format(tableName=tableName))
        connection.close()

        countryDF, yearList, wdiList = PortfolioProject.pivotEduData(countryName)

        #   Using 'GDP (current US$)' from WDI Data: 'NY.GDP.MKTP.CD' is the 'Indicator Code'.
        columnNames = PortfolioProject.WDI_SOURCE_DATA['columnNames']
        wdiDataFrame = PortfolioProject.WDI_SOURCE_DATA['wdiDataFrame']
        if DEBUG:
            print("\nwdiDataFrame:\n", wdiDataFrame)

        dataFrame = wdiDataFrame[(wdiDataFrame[columnNames[0]] == countryName) & (wdiDataFrame['Indicator Code'] == 'NY.GDP.MKTP.CD')]
        values = list(dataFrame.values)
        tableData = []
        rowIdx = 0
        while rowIdx < len(values[0]):
            if columnNames[rowIdx].isnumeric():
                try:
                    val = float(values[0][rowIdx])
                except:
                    val = None
                tableData.append((int(columnNames[rowIdx]), val))
            rowIdx += 1

        if DEBUG:
            print('\nExtracted GDP Data:\n', dataFrame.head(25))
            print('\tDimensions:\t', dataFrame.size)
            print('\t')
            #   for value in dataFrame.values:
            #       print(value)

        if DEBUG:
            rowIdx = 0
            while rowIdx < len(tableData):
                print(str(rowIdx) + '\tyearList[rowIdx]:\t' + str(yearList[rowIdx]) +
                      '\twdiList[rowIdx]:\t' + str(wdiList[rowIdx]) + '\ttableData[rowIdx]:\t' + str(tableData[rowIdx]))
                rowIdx += 1
                #   yearList, wdiList, tableData

        connection = connect(countryDbPath)
        rowIdx = 0
        while rowIdx < len(tableData):
            connection.execute("""INSERT INTO "{tableName}" ("Year", "Primary Enrollment", "GDP")
                                VALUES (?, ?, ?);""".format(tableName=tableName),
                               (yearList[rowIdx], wdiList[rowIdx], tableData[rowIdx][1]))
            rowIdx += 1
        connection.commit()
        connection.close()

        #   Produce the CSV file from the table:
        countryCsvPath = CountryData.DataFolder + '/' + 'Assignment8_' + countryName + '.csv'
        if isfile(countryCsvPath):
            if not force:
                report['Error'] = "Table for specified country already exists:\t" + tableName
                return report
        connection = connect(countryDbPath)
        dataFrame = pandas.read_sql("""SELECT * FROM "{}";""".format(tableName), connection)
        dataFrame.to_csv(countryCsvPath, index=False)


class BarCharts:
    """
    Started:    2026-09-10
    Source:     Claude.ai
    Prompt:     Write a Python method which uses matplotlib.pyplot to display a barchart of a
                time sequence of measurements of two or more variables.  The time sequence
                should of course be on the horizontal axis.
    """

    DataFolder = environ['HOME'] + '/ACTIVITIES/Graduate School/CSU Global/Advanced Data Analytics Certificate/Courses/MIS 505 - Data Wrangling/Assignments/Week 8/production data'

    @staticmethod
    def plot_grouped_bar_timeseries(time_labels, data_dict, countryName: str=None,
                                    title="Measurements Over Time",
                                      xlabel="Time", ylabel="Value", figsize=(10, 6)):
        """
        Display a grouped bar chart of two or more variables measured over a time sequence.
        """
        if len(data_dict) < 2:
            raise ValueError("data_dict must contain at least two variables to compare.")

        n_vars = len(data_dict)
        n_points = len(time_labels)

        # Validate that all variable series match the number of time points
        for name, values in data_dict.items():
            if len(values) != n_points:
                raise ValueError(f"Variable '{name}' has {len(values)} values, "
                                  f"expected {n_points} (one per time label).")

        x = numpy.arange(n_points)          # base positions for each time point
        bar_width = 0.8 / n_vars         # width of each individual bar

        fig, ax = pyplot.subplots(figsize=figsize)

        for i, (var_name, values) in enumerate(data_dict.items()):
            offset = (i - (n_vars - 1) / 2) * bar_width
            ax.bar(x + offset, values, width=bar_width, label=var_name)

        ax.set_xticks(x)
        ax.set_xticklabels(time_labels, rotation=45, ha="right")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title + ": " + countryName)
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        fig.tight_layout()
        pyplot.show()

        return fig, ax


    @staticmethod
    def plotCountryData(countryName: str):
        dbFileName = 'Assignment8_' + countryName + '.sqlitedb'
        dbFilePath = BarCharts.DataFolder + '/' + dbFileName
        report = {}
        if not isfile(dbFilePath):
            report['Error'] = "DB file for country not found:\t" + dbFilePath
            return report
        tableName = 'Assignment8_' + countryName
        connection = connect(dbFilePath)
        rows = connection.execute("""SELECT * FROM "{}";""".format(tableName)).fetchall()
        connection.close()
        dataMap = OrderedDict()
        timePoints = []
        measurements = {
            'Primary Enrollment': [],
            'GDP': []
        }
        for row in rows:
            if row[0] > 2000:
                timePoints.append(str(row[0]))
                measurements['Primary Enrollment'].append(100000*row[1] if row[1] is not None else 0)
                measurements['GDP'].append(row[2] if row[2] is not None else 0)
            dataMap[row[0]] = {
                'Year': row[0],
                'Primary Enrollment': row[1],
                'GDP': row[2]
            }
        BarCharts.plot_grouped_bar_timeseries(time_labels=timePoints, data_dict=measurements,
                                              countryName=countryName)
        return dataMap


if __name__ == "__main__":
    print("\nRunning:\t" + MODULE_NAME)

    if not isdir(PortfolioProject.DataFolder):
        print("\nFolder containing downloaded data does not exist:\t" + PortfolioProject.DataFolder, file=stderr)

    PortfolioProject.load_WDI_Data()
    PortfolioProject.load_PRM_ENRL()
    CountryData.initializeStorage()
    PortfolioProject.makeAssignment_8_DB_n_CSV('Argentina')

