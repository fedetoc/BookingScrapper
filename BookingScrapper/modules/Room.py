from bs4 import BeautifulSoup
from .Locator import Locator
from .Hotel import Hotel
import unidecode

class Room:
    nombre = ""
    metrosCuadrados = None
    cantidadCamasIndividuales = None
    cantidadCamasDoble = None
    cantidadCamasGrandes = None
    cantidadCamasExtraGrandes = None
    cantidadFutones = None
    cantidadSofaCamas = None
    __locators = {
        "MetrosCuadrados": Locator('div', 'data-name-en', 'room size')
    }

    def __init__(self, hotel: Hotel):
        self.hotel_ref = hotel
        
    def parse_html(self, html):
        soup = BeautifulSoup(f'<div>{html}</div>', 'html.parser')
        if not soup.tr is None:
            self.__html_soup = soup.tr.find_all('td')[0]
        else:
            self.__html_soup = soup
        self.nombre = self.__get_name()
        self.metrosCuadrados = self.__get_squared_meters()
        ammount_beds = self.__get_ammount_of_beds()
        self.cantidadFutones = ammount_beds[0]
        self.cantidadSofaCamas = ammount_beds[1]
        self.cantidadCamasDoble = ammount_beds[2]
        self.cantidadCamasGrandes = ammount_beds[3]
        self.cantidadCamasExtraGrandes = ammount_beds[4]
        self.cantidadCamasIndividuales = ammount_beds[5]
        return self

    def __get_name(self):
        room_name = self.__html_soup.find(
                    lambda tag: tag.name == "a" and 
                        (tag.has_attr("data-room-id") or (tag.has_attr("id") and "room_type_id" in tag['id']))
            ).span.get_text()
        return room_name

    def __get_squared_meters(self):
        sq_meters_el = self.__find_el_by_locator_key("MetrosCuadrados")
        if sq_meters_el is None:
            return -1
        else:
            return self.__parse_number(sq_meters_el.span.get_text(), [" m2"])

    def __get_ammount_of_beds(self):
        all_room_bed_wrappers = self.__html_soup.find(
                lambda tag: tag.name == "div" and ("bed-types-wrapper" in tag['class'][0])
            )
        ammount_fouton = 0
        ammount_bed_couch = 0
        ammount_individual_beds = 0
        ammoung_double_bed = 0
        ammount_big_bed = 0
        ammount_extrabig_bed = 0
        if all_room_bed_wrappers is not None:
            all_room_bed_els = all_room_bed_wrappers.ul.find_all("li")
            beds_txt = []
            for li_el in all_room_bed_els:
                span_els = li_el.find_all("span")
                for span in span_els:
                    beds_txt.append(span.get_text().strip())
            for bed in beds_txt:
                txt = bed.replace('s', '')
                curr_amm = int(txt[0])
                if "futón" in txt:
                    ammount_fouton = ammount_fouton+curr_amm
                elif "ofá cama" in txt:
                    ammount_bed_couch = ammount_bed_couch+curr_amm
                elif "cama individual" in txt:
                    ammount_individual_beds = ammount_individual_beds+curr_amm
                elif "cama doble extragrande" in txt:
                    ammount_extrabig_bed = ammount_extrabig_bed+curr_amm
                elif "cama doble grande" in txt:
                    ammount_big_bed = ammount_big_bed+curr_amm
                elif "cama doble" in txt:
                    ammoung_double_bed = ammoung_double_bed+1
        return (ammount_fouton, ammount_bed_couch, ammoung_double_bed, ammount_big_bed, ammount_extrabig_bed, ammount_individual_beds)
    
    def __find_el_by_locator_key(self, key:str, all_list = False):
        loc = self.__locators[key]
        if all_list == True:
            return self.__html_soup.find_all(loc.tag, {loc.attr: loc.attr_val})
        return self.__html_soup.find(loc.tag, {loc.attr: loc.attr_val})

    def __parse_number(self, price:str, chars_to_remove:list, ret_int = True):
        decode_price = unidecode.unidecode(price)
        cleaned_price = decode_price
        for char in chars_to_remove:
            cleaned_price = cleaned_price.replace(char, '')
        if ret_int == False:
            return float(cleaned_price)
        return int(cleaned_price)

    def get_room_data(self):
        return (self.nombre, self.metrosCuadrados, self.cantidadFutones, self.cantidadSofaCamas,
                self.cantidadCamasIndividuales, self.cantidadCamasDoble, self.cantidadCamasGrandes, self.cantidadCamasExtraGrandes)
