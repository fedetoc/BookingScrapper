from bs4 import BeautifulSoup
from .Locator import Locator
import unidecode

class Hotel:
    nombre = ""
# Agregar si tiene traslado del aeropuerto, pileta, gimnasio y estacionamiento
    stars = None
    review_score = None
    cant_comentarios = None
    distanciadelcentro = None
    distanciadelaplaya = None
    bookingLink = None
    tiene_estacionamiento = None
    estacionamiento_gratis = None
    tiene_gim = None
    tiene_pileta = None
    traslado_aeropuerto_gratis = None
    __locators = {
        "Nombre": Locator('div', 'data-testid', 'title'),
        "Impuesto": Locator('div', 'data-testid', 'taxes-and-charges'),
        "Puntuacion": Locator('div', 'data-testid', 'review-score'),
        "Estrellas": Locator('div', 'data-testid', "rating-stars", "rating-squares"),
        "DistanciaCentro": Locator('span', 'data-testid', "distance"),
        "Link": Locator('a', 'data-testid', 'title-link')
    }
    
    @staticmethod
    def parse_html(html):
       hotel = Hotel()
       hotel.__html_soup = BeautifulSoup(html, 'html.parser')
       hotel.nombre = hotel.__get_name()
       hotel.bookingLink = hotel.__get_link()
       hotel.stars = hotel.__get_stars()
       hotel.nombre = hotel.__get_name()
       hotel.distanciadelcentro, hotel.distanciadelaplaya = hotel.__get_center_and_beach_distances()
       hotel.review_score, hotel.cant_comentarios = hotel.__get_score_and_comments_ammount()
       return hotel
    
    def __get_stars(self):
        stars_el = self.__find_el_by_locator_key("Estrellas")
        if stars_el is None:
            return -1
        else:
            return len(stars_el.find_all("span"))

    def __get_name(self):
        name_el = self.__find_el_by_locator_key("Nombre")
        return name_el.contents[0]

    def __get_link(self):
        link_el = self.__find_el_by_locator_key("Link")
        return link_el['href']
        
    def __get_center_and_beach_distances(self):
        dist_el = self.__find_el_by_locator_key("DistanciaCentro")
        if dist_el is None:
            return (-1, -1)
        dist_text = dist_el.get_text()
        if " km" in dist_text:
            distancia_parsed = self.__parse_number(dist_text.replace(",", "."), ["a ", " km del centro"], ret_int=False) * 1000
        else:
            distancia_parsed = self.__parse_number(dist_text.replace(",", "."), ["a ", " m del centro"], ret_int=False)

        dist_playa_parent_el = dist_el \
                                .parent \
                                .parent \
                                .parent \
                                .next_sibling
        if dist_playa_parent_el is None:
            return (distancia_parsed, -1)
        dist_playa_el = dist_playa_parent_el \
                            .contents[0] \
                            .contents[0] \
                            .contents[1]
        if dist_playa_el is None:
            return (distancia_parsed, -1)
        dist_playa_text = dist_playa_el.get_text()
        if dist_playa_text == "Frente a la playa":
            dist_playa = 0
        elif " m " in dist_playa_text:
            dist_playa = self.__parse_number(dist_playa_text, ["A ", " m de la playa"])
        elif " km " in dist_playa_text:
            dist_playa = self.__parse_number(
                    dist_playa_text.replace(",", "."), ["A ", " km de la playa"], ret_int = False
            ) * 1000
        else:
            dist_playa = -1
        return (distancia_parsed, dist_playa)

    def __get_score_and_comments_ammount(self):
        score_el = self.__find_el_by_locator_key("Puntuacion")
        if score_el is None:
          return (-1, -1.0)
        comments_text = score_el \
            .select_one("div div:nth-of-type(2)") \
            .select_one("div div:nth-of-type(2)") \
            .text
        score_text = score_el.find("div").get_text()[-3:]
        comments_parsed = self.__parse_number(comments_text, [".", "s", " comentario"])
        score_parsed = float(score_text.replace(",", "."))
        return (score_parsed, comments_parsed)
    
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

    def get_hotel_data(self):
        return (
            self.nombre, self.stars, self.review_score, \
            self.cant_comentarios, self.distanciadelcentro, \
            self.distanciadelaplaya, self.tiene_estacionamiento, \
            self.estacionamiento_gratis, self.tiene_gim, \
            self.tiene_pileta, self.traslado_aeropuerto_gratis, self.bookingLink
        )

    def set_highlights(self, estacionamiento:bool = None, estac_gratis:bool = None, gim:bool = None, pileta:bool = None, traslado:bool = None):
        if not estacionamiento is None:
            self.tiene_estacionamiento = estacionamiento
            if not estac_gratis is None:
                self.estacionamiento_gratis = estac_gratis
        if not gim is None:
            self.tiene_gim = estacionamiento    
        if not pileta is None:
            self.pileta = pileta
        if not traslado is None:
            self.traslado = traslado

    def parse_highlights_html(self, wrapper_html:str):
        html = BeautifulSoup(wrapper_html, 'html.parser')
        highlights_els = html.find_all("li")
        highlights_texts = [el.div.div.div.span.div.span.get_text().lower() for el in highlights_els]
        for text in highlights_texts:
            if "pileta" in text:
                self.tiene_pileta = True
            elif "estacionamiento" in text:
                self.tiene_estacionamiento = True
                if "gratuito" in text:
                    self.estacionamiento_gratis = True
            elif "gimnasio" in text:
                self.tiene_gim = True
            elif "transfer al aeropuerto (gratis)" in text:
                self.traslado_aeropuerto_gratis = True
            else:
                continue;