# Booking Scrapper

## Purpose

This set of scripts is aimed to provide an interface for scrapping hotels and rooms from Booking.com, by providing the start and end dates, as well as the destination. Currently, prices and taxes are returned in USD. This is intended to be used just for academic purposes.

## Prerrequisites

BookingScrapper relies on the following libraries installed to work properly:

* selenium (v 4.27 or later)
* beautifulsoup4 (v 4.12 or later)
* requests (v 2.32 or later)
* unidecode (v 1.3 or later)
* sqlite (v 3.45 or later)

Since this is not a library, you can copy the folder BookingScrapper into the root directory of your project.

## Usage

### Getting the scraper

The following code will import the needed libraries and get an scraper object that will initialize the webdriver and prepare the request to get the Booking webpage.

```

    # Importing libraries
    from BookingScrapper.main.BookingScrapper import BookingScrapper
    from datetime import date

    # Saving basic parameters
    destination = "Miami Beach"
    checkin_date = date.fromisoformat("2025-05-01")
    checkout_date = date.fromisoformat("2025-05-29")

    # Getting the scrapper
    scraper = BookingScrapper(destination, checkin_date, checkout_date)
    
```

### Fire request and acquire hotel's data

The following will send the request containing the selected dates and destination, and begin scrapping the data from the main search feed. Note that this will only capture hotel's general data available in that feed. Data about amenities such as pool or parking lot for each hotel are only available in the highlights section upon entering to the hotel page. Such data won't be captured at this step.

This takes as argument the number of pages of data required, which are an abstraction of the number of scrolls to the bottom the application needs to perform to allow for more hotels to be loaded and captured.

```

    # Get hotels data
    hotels = scraper.get_hotels(1)

```

#### RETURN

The above code returns a list of Hotel objects with the captured data.

### Get room offers

The following will send a request for each hotel obtained in the previous step to extract the rooms data on each hotel page. It will also retrieve ammenities data for the scrapped hotels.

```

    # Get room offers
    offers = scraper.get_room_offers()

```

This code will call get_hotels in case it wasn't previously called, since it needs the link to each hotel page.

#### RETURN

A list of dictionaries with the following keys:

* Room: This contains a Room object with all the data available regarding a particular hotel room. It is possible to get the hotel it pertains through the .hotel_ref attribute.
* Offers: Contains a list of RoomOffer objects with all the offers data available for each hotel room, including price before tax and taxes. It is possible to get the room it pertains through the .room_ref attribute.

### Save the data to sqlite db

The following will save all the acquired data from previous steps to a sqlite db in the specified directory. This is just intended to provide an stagging area from where the data can be later migrated or analysed using other tools. It is not intended as a permanent repository.

```

    # Connect and save to sqlite db
    db_obj = scraper.save_to_db_sqlite('./database')

```

It accepts as argument the complete or relative path where the db will be located. If relative path is provided, it will take the project path from where this is called as root. If the directory specified already exists, it will try to connect to the db, drop the tables if exist and recreate them inserting the new data.

The database created contains the following three tables that can be later retrieved:

* hotel: Contains the hotel data scrapped
* habitacion: Contains the rooms data scrapped
* oferta: Contains the RoomOffers data scrapped

#### RETURN

A DatabaseHandler object that will be later used to retrieve the data.

### Retrieve the data from the sqlite db

There are a series of methods that can be called to retrieve the data from the sqlite db created. For example, to count the ammount of rows from a particular table you can call the following:

```

    # Get the number of room offers from oferta table
    number_of_rows = db_obj.get_row_count("oferta")
    print(str(number_of_rows)) # 48

```

The following retrieves all the data from a particular table. It accepts as arguments the table name and a boolean to indicate wether to include the field names in the output:

```

    # Get all hotels data from hotel table
    hotels_data = db_obj.get_all_cols_and_rows_from_tbl("hotel", True)

```

You can easily turn the output into a Pandas dataframe:

```

    # Turn hotels_data into a pandas Dataframe
    import Pandas as pd
    df_hoteles = pd.DataFrame(hotels_data[0], columns=hotels_data[1]).set_index("hotel_id")

```

Finally, the following code can be used to merge all the data stored in the db into a single Pandas Dataframe:

```

    # Turn db data into a pandas Dataframe
    data_hotels = db_obj.get_all_cols_and_rows_from_tbl("hotel", True)
    data_rooms = db_obj.get_all_cols_and_rows_from_tbl("habitacion", True)
    data_offers = db_obj.get_all_cols_and_rows_from_tbl("oferta", True)
    df_hotels = pd.DataFrame(data_hotels[0], columns=data_hotels[1]).set_index("hotel_id")
    df_rooms = pd.DataFrame(data_rooms[0], columns=data_rooms[1])
    df_offers = pd.DataFrame(data_offers[0], columns=data_offers[1])

    # Merge the data into a single Dataframe
    df_main = df_hotels \
            .merge(df_rooms, on="hotel_id", how="outer").set_index("habitacion_id") \
            .merge(df_offers, on="habitacion_id", how="outer").set_index("oferta_id")
    df_main.rename(columns={"nombre_x": "nombre_hotel", "nombre_y": "nombre_habitacion"}, inplace=True)

```

### Close db connection

Once finished with the db operations, it's important to close it to avoid memory leakage. You can do so by calling the following:

```

    # Close sqlite db connection
    db_obj.close_connection()

```


## Disclaimer

This was created to be used for academic purposes only, I'm not held responsible for the use or missuse of the code saved in this repo.  

## Author

Federico Tocco