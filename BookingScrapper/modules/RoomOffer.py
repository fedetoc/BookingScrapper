from bs4 import BeautifulSoup
from .Locator import Locator
from .Room import Room
class RoomOffer:
# Agregar politica de pago por adelantado
    cant_huespedes_permitidos = None
    desayuno_incluido = None
    cancela_gratis = None
    precio_antes_impuestos = None
    impuestos = None
    __locators = {
        "Huespedes": Locator("span", "class", "c-occupancy-icons__multiplier-number"),
        "HuespedesAlternativo": Locator("i", "class", "bicon bicon-occupancy"),
        "Desayuno": Locator("div", "class", "bui-list__description"),
        "CancelacionFlexible": Locator("div", "data-testid", "cancellation-policy"),
        "SubtituloDePolitica": Locator("div", "data-testid", "policy-subtitle")
    }
    __policies_el = None
    
    def __init__(self, room: Room):
        self.room_ref = room

    def parse_html(self, html):
        self.__html_soup = BeautifulSoup(f'{html}', 'html.parser')
        self.__first_room_offer = self.__is_first_row()
        self.precio_antes_impuestos = self.__get_price()
        self.cant_huespedes_permitidos = self.__get_ammount_occupants()
        self.impuestos = self.__get_taxes()
        self.desayuno_incluido = self.__is_breakfast_included()
        self.cancela_gratis = self.__is_flexible_cancellation()
        return self
        
    def __get_price(self):
        
        try:
            price = int(self.__html_soup.find('tr')["data-hotel-rounded-price"])
        except err:
            print(self.__html_soup)
            raise(err)
        return price

    def __get_taxes(self):
        taxes_el = self.__row_cells[1+self.__first_room_offer] \
                    .find(lambda tag: tag.has_attr('data-excl-charges-raw'))
        return float(taxes_el.get('data-excl-charges-raw'))

    def __get_ammount_occupants(self):
        cant_huespedes_el = self.__find_child_el_by_locator_key(
                self.__row_cells[0+self.__first_room_offer], "Huespedes"
        )
        if cant_huespedes_el is None:
            return len(
                self.__find_child_el_by_locator_key(
                    self.__row_cells[0+self.__first_room_offer],"HuespedesAlternativo", True
                )
            )
        else:
            return int(cant_huespedes_el.get_text())
    
    
    def __is_breakfast_included(self):
        if self.__policies_el is None:
            self.__set_policies_el()
        todas_las_politicas = self.__policies_el.find_all("li")
        primera_politica_el = self.__find_child_el_by_locator_key(
            todas_las_politicas[0], "Desayuno"
        )
        if primera_politica_el is not None:
            primera_politica_text = primera_politica_el.get_text()
            if "desayuno" in primera_politica_text.lower() and "incluido" in primera_politica_text:
                return True
        return False

    def __is_flexible_cancellation(self):
        if self.__policies_el is None:
            self.__set_policies_el()
        canc_el = self.__find_child_el_by_locator_key(
                    self.__policies_el,"CancelacionFlexible"
        )
        if not canc_el is None:
            canc_text = self.__find_child_el_by_locator_key(
                        canc_el,
                        "SubtituloDePolitica") \
                        .span.strong.get_text()
            if "Cancelación gratis" in canc_text:
                return True
        return False
    
    def __is_first_row(self):
        row_cells = self.__html_soup.find_all('td')
        self.__row_cells = row_cells
        if row_cells[0].has_attr('rowspan'):
            return 1
        return 0

    def __set_policies_el(self):
        self.__policies_el = self.__row_cells[2+self.__first_room_offer].div.ul

    def __find_child_el_by_locator_key(self, el, key:str, all_list = False):
        loc = self.__locators[key]
        if all_list == True:
            return el.find_all(loc.tag, {loc.attr: loc.attr_val})
        return el.find(loc.tag, {loc.attr: loc.attr_val})

    def get_room_offer_data(self):
        return (self.cant_huespedes_permitidos, self.desayuno_incluido, self.cancela_gratis,
               self.precio_antes_impuestos, self.impuestos)