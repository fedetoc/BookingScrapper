from requests import Session, Request
import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
import time
from ..modules.Hotel import Hotel
from ..modules.Room import Room
from ..modules.RoomOffer import RoomOffer
from ..modules.DatabaseHandler import DatabaseHandler

class BookingScrapper:
    __base_url = "https://www.booking.com/searchresults.es-ar.html"
    __full_url = ""
    __xpath_dic = {
        "DialogMainPage": '//div[@role = "dialog" and not(@aria-label = "Ver alojamiento en el mapa")]',
        "LoadMoreResultsBtn": '//button/span[contains(text(),"Cargar más resultados")]/parent::button',
        "HotelCard": '//div[@data-testid = "property-card"]',
        "LastHotelCard": '//div[@data-testid = "property-card"][last()]',
        'NextHotelByClass': '//div[@data-testid = "property-card" and @class = "{HOTEL_CLASS}"]//following-sibling::div[@data-testid = "property-card"]',
        'BtnLoadMoreResults':  '//button/span[contains(text(),"Cargar más resultados")]/parent::button',
        'RoomTableRow': '//table[@id="hprt-table"]/tbody/tr',
        'RoomTableRowAllCells': '//td',
        'RoomTableLeadingRow': '//td[1][@rowspan]',
        'HotelHighlights': '//div[@data-testid="property-most-popular-facilities-wrapper"]',
        'Error404': '//div[@class="wrapper-404"]'
    }
    __hotel_list = []
    __rooms_and_offers_list = []
    __db_tables_schema = {"hotel":
              [
                ("hotel_id", "integer"),
                ("nombre", "text"),
                ("estrellas", "integer"),
                ("puntuacion_resenias", "integer"),
                ("cant_comentarios ", "integer"),
                ("distancia_centro", "integer"),
                ("distancia_playa", "integer"), 
                ("tiene_estacionamiento", "integer"),
                ("estacionamiento_gratis", "integer"),
                ("tiene_gim", "integer"),
                ("tiene_pileta", "integer"),
                ("traslado_aeropuerto_gratis", "integer"), 
                ("link_booking", "text")
              ],
           "habitacion":
              [
                ("habitacion_id", "integer"),
                ("hotel_id", "integer"),
                ("nombre", "text"),
                ("metros_cuadrados", "integer"),
                ("cantidad_futones ", "integer"),
                ("cantidad_sofa_camas", "integer"),
                ("cantidad_camas_individuales", "integer"),
                ("cantidad_camas_dobles", "integer"), 
                ("cantidad_camas_grandes", "integer"),
                ("cantidad_camas_extragrandes", "integer")
              ],
           "oferta":
             [
                ("oferta_id", "integer"),
                ("habitacion_id", "integer"),
                ("cant_huespedes_permitidos", "integer"),
                ("desayuno_incluido", "integer"),
                ("cancela_gratis", "integer"),
                ("precio_antes_impuestos", "real"),
                ("impuestos", "real")
              ]
         } 
    
    def __init__(self, location:str, checkin_date:datetime.date, checkout_date:datetime.date):
        self.location = location
        self.checkin_date = checkin_date
        self.checkout_date = checkout_date
        self.currency = "USD"
        self.__driver = self.__get_webdriver() 

    def __get_webdriver(self):
        s = Session()
        dr = webdriver.Chrome()
        return dr

    def __get_webelement_by_xpath(self, xpath:str, els_list = True):
        if els_list:
            return self.__driver.find_elements(By.XPATH, xpath)
        else:
            return self.__driver.find_element(By.XPATH, xpath)

    def __get_webelement_by_xpath_key(self, xpath_key:str, els_list = True):
        if els_list:
            return self.__driver.find_elements(By.XPATH, self.__xpath_dic[xpath_key])
        else:
            return self.__driver.find_element(By.XPATH, self.__xpath_dic[xpath_key])

    def __get_child_webelement_by_tag(self, tag:str, el: WebElement ,els_list = True):
        if els_list:
            return el.find_elements(By.TAG_NAME, tag)
        else:
            return el.find_element(By.TAG_NAME, tag)

    def __scroll_to_element(self, el: WebElement):
        ActionChains(self.__driver) \
            .scroll_to_element(el) \
            .perform()

    def __scroll_to_element_by_key(self, xpath_key: str):
        el = self.__get_webelement_by_xpath_key(xpath_key, els_list = False)
        ActionChains(self.__driver) \
            .scroll_to_element(el) \
            .perform()

    def __click_btn_with_script(self, btn_el: WebElement):
        btn_class = btn_el.get_attribute('class').replace(' ', '.')
        self.__driver.execute_script(f"document.querySelector('button.{btn_class}').click()")
        
    def __is_elem_present(self, xpath:str):
        el = self.__get_webelement_by_xpath(xpath)
        if len(el) == 0:
            return False
        return True

    def __close_dialog_main_page(self, wait_after: int):
        dialog_xpath = self.__xpath_dic["DialogMainPage"]
        if self.__is_elem_present(dialog_xpath):
            self.__get_webelement_by_xpath(dialog_xpath + '//button', els_list = False).click()
            time.sleep(wait_after); # 2

    def __extract_hotel_cards_html(self, pages: int, wait: int):
        prop_elements = []
        amm_hotel_els = 0
        for i in range(pages):
            btn_load_more_xpath = self.__xpath_dic["BtnLoadMoreResults"]
            if self.__is_elem_present(btn_load_more_xpath) == False:
                self.__scroll_to_element_by_key("LastHotelCard")
                prop_elements = self.__get_webelement_by_xpath_key("HotelCard")
                if len(prop_elements) == amm_hotel_els:
                    break;
                amm_hotel_els = len(prop_elements)
            else:
                btn_el = self.__get_webelement_by_xpath_key("BtnLoadMoreResults", els_list=False)
                self.__scroll_to_element(btn_el)
                time.sleep(2)
                self.__click_btn_with_script(btn_el)
            time.sleep(wait)
        return [Hotel.parse_html(f'<div>{elem.get_attribute("innerHTML")}</div>') for elem in prop_elements]

    def prepare_request (self):
        method = 'GET'
        parameters = {
          'ss': self.location,
          'lang': 'es-ar',
          'sb': '1',
          'src_elem' : 'sb',
          'src': 'index', 
          'dest_type': 'city', 
          'checkin': self.checkin_date.strftime('%Y-%m-%d'),
          'checkout': self.checkout_date.strftime('%Y-%m-%d'), 
          'group_adults': '2',
          'no_rooms': '1',
          'group_children': '0',
          'selected_currency': self.currency,
          'nflt': 'ht_id=204'}
        req = Request(method, self.__base_url, params =parameters).prepare()
        self.__full_url = req.url

    def make_request (self, wait_secs = 5):
        if self.__full_url == "":
            self.__prepare_request()
        self.__driver.get(self.__full_url)
        time.sleep(wait_secs)     

    def get_hotels(self, pages:int, wait_before_page_change = 5):
        self.prepare_request()
        self.make_request()
        self.__close_dialog_main_page(2)
        self.__hotel_list = self.__extract_hotel_cards_html(pages, wait_before_page_change)
        return self.__hotel_list

    def get_room_offers(self, wait_secs_after_load = 5):
        if len(self.__rooms_and_offers_list) != 0:
            return self.__rooms_and_offers_list
        if len(self.__hotel_list) == 0:
            get_hotels(5)
        results = []
        for hotel in self.__hotel_list:
            fail_to_fetch = False
            self.__driver.get(hotel.bookingLink);
            error_load_el = self.__xpath_dic["Error404"]
            if self.__is_elem_present(error_load_el):
                retries = list(range(3))
                for i in retries:
                    self.__driver.get(hotel.bookingLink);
                    time.sleep(wait_secs_after_load);
                    if self.__is_elem_present(error_load_el) == False:
                        break;
                    if i+1 == len(retries):
                        fail_to_fetch = True
                        break;
            if fail_to_fetch:
                continue;
            time.sleep(wait_secs_after_load);
            offers_list = self.__get_webelement_by_xpath_key("RoomTableRow")
            highlights_el = self.__get_webelement_by_xpath_key("HotelHighlights")[0]
            hotel.parse_highlights_html(highlights_el.get_attribute('outerHTML'))
            first_room_offer = 1
            result_dic = {
                "Room": None,
                "Offers": []
            }
            for it in range(len(offers_list)):
                el = offers_list[it]
                outer_html = el.get_attribute('outerHTML')
                first_cell = self.__get_child_webelement_by_tag('td', el)[0]
                if not first_cell.get_attribute('rowspan') is None:
                    result_dic['Room'] = Room(hotel).parse_html(outer_html)
                    result_dic["Offers"] = []
                offer = RoomOffer(result_dic['Room']).parse_html(outer_html)
                result_dic["Offers"].append(offer)
                if len(offers_list)-1 == it:
                    results.append(result_dic.copy())
                    continue;
                if len(offers_list)-1 > it+1:
                    first_cell_next_row = self.__get_child_webelement_by_tag('td', offers_list[it+1])[0]
                    if (not first_cell_next_row.get_attribute('rowspan') is None):
                        results.append(result_dic.copy())
        self.__rooms_and_offers_list = results
        return results
        
    def save_to_db_sqlite(self, db_dir:str = None):
        if len(self.__rooms_and_offers_list) == 0:
            raise(Exception("No se ha encontrado datos para guardar en la db"))
            return;
        db_name = 'booking'
        dbh = DatabaseHandler(db_name, db_dir, self.__db_tables_schema)
        last_hotel = None
        data_to_insert = {
            "hotel": [],
            "habitacion": [],
            "oferta": []
        }
        hotel_id = 0
        room_id = 1
        room_offer_id = 1
        for off_item in self.__rooms_and_offers_list:
            room, offers = tuple(off_item.values())
            if room.hotel_ref != last_hotel:
                hotel_id = hotel_id + 1
                hotel_det = (hotel_id,) + room.hotel_ref.get_hotel_data()
                data_to_insert["hotel"].append(hotel_det)
                last_hotel = room.hotel_ref

            room_det = (room_id, hotel_id,) + room.get_room_data()
            data_to_insert["habitacion"].append(room_det)

            for offer in offers:
                offer_det = (room_offer_id, room_id,) + offer.get_room_offer_data()
                data_to_insert["oferta"].append(offer_det)
                room_offer_id = room_offer_id + 1
                
            room_id = room_id + 1         
        
        tablas_a_insertar = list(data_to_insert.keys())
        dbh.eliminate_tables(tablas_a_insertar)
        dbh.create_tables(self.__db_tables_schema)
        for tbl in tablas_a_insertar:
         dbh.insert_into_table(tbl, data_to_insert[tbl])
        
        return dbh
                
                