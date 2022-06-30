import json
import logging

import re
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, NOTEBOOK, STEREO_SYSTEM, KEYBOARD, \
    MOUSE, WEARABLE, TABLET, REFRIGERATOR, HEADPHONES, \
    KEYBOARD_MOUSE_COMBO, VIDEO_GAME_CONSOLE, MONITOR, \
    MEMORY_CARD, GAMING_CHAIR, STORAGE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, \
    USB_FLASH_DRIVE, RAM, TELEVISION, AIR_CONDITIONER, OVEN, WASHING_MACHINE, \
    ALL_IN_ONE, VACUUM_CLEANER, PRINTER, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MercadoLibreChile(Store):
    categories_code = [('MLC1051', 'Celulares y Telefonía', None),
                       ('MLC1648', 'Computación', None),
                       ('MLC1000', 'Electrónica, Audio y Video', None),
                       ('MLC1574', 'Hogar y Muebles', None),
                       ('MLC1010', 'Audio', None),
                       ('MLC5054', 'Cables', None),
                       ('MLC4632', 'Controles Remotos', None),
                       ('MLC430918', 'Cables y Hubs USB', None),
                       ('MLC430687', 'Notebooks y Accesorios', NOTEBOOK),
                       ('MLC454379', 'Periféricos de PC', None),
                       ('MLC433676', 'Tablets y Accesorios', TABLET),
                       ('MLC159241', 'Lápices Touch', None),
                       ('MLC159232', 'Teclados', KEYBOARD),
                       ('MLC1714', 'Mouses', MOUSE),
                       ('MLC1713', 'Teclados', KEYBOARD),
                       ('MLC373735', 'Trackpads', None),
                       ('MLC6593', 'Cables y Adaptadores', None),
                       ('MLC11878', 'Candados de Seguridad', None),
                       ('MLC3813', 'Accesorios para Celulares', None),
                       ('MLC417704', 'Smartwatches y Accesorios', WEARABLE),
                       ('MLC417755', 'Cargadores', None),
                       ('MLC434353', 'Mallas', None),
                       ('MLC436011', 'Adaptadores', None),
                       ('MLC4922', 'Cables de Datos', None),
                       ('MLC432437', 'Carcasas, Fundas y Protectores', None),
                       ('MLC5546', 'Cargadores', None),
                       ('MLC5549', 'Otros', None),
                       ('MLC157684', 'Cargadores con Cable', None),
                       ('MLC157688', 'Inalambrico', None),
                       ('MLC49334', 'Para TV', None),
                       ('MLC49342', 'Otros', None),
                       ('MLC116538', 'Smartwatches', WEARABLE),
                       ('MLC85756', 'Accesorios', None),
                       ('MLC82067', 'Tablets', TABLET),
                       ('MLC430637', 'PC de Escritorio', None),
                       ('MLC3690', 'Accesorios para Audio y Video', None),
                       ('MLC157822', 'Netbooks', NOTEBOOK),
                       ('MLC1652', 'Notebooks', NOTEBOOK),
                       ('MLC1055', 'Celulares y Smartphones', CELL),
                       ('MLC5726', 'Electrodomésticos', None),
                       ('MLC1430', 'Vestuario y Calzado', None),
                       ('MLC1012', 'Audio Portátil y Accesorios',
                        STEREO_SYSTEM),
                       ('MLC3697', 'Audífonos', HEADPHONES),
                       ('MLC440071', 'Artefactos de Cuidado Personal', None),
                       ('MLC1581', 'Pequeños Electrodomésticos', OVEN),
                       ('MLC1667', 'Cámaras Web', None),
                       ('MLC430630', 'Mouses y Teclados', None),
                       ('MLC1053', 'Telefonía Fija e Inalámbrica', None),
                       ('MLC432435', 'Colgantes y Soportes', None),
                       ('MLC439917', 'Apoya Celulares', None),
                       ('MLC439919', 'Porta Celulares', None),
                       ('MLC157686', 'Portatiles', None),
                       ('MLC157694', 'Carcasas y Fundas', None),
                       ('MLC175454', 'Cases', None),
                       ('MLC12953', 'Láminas Protectoras', None),
                       ('MLC1144', 'Consolas y Videojuegos', None),
                       ('MLC1500', 'Construcción', None),
                       ('MLC1132', 'Juegos y Juguetes', None),
                       ('MLC1582', 'Iluminación para el Hogar', None),
                       ('MLC177170', 'Seguridad para el Hogar', None),
                       ('MLC1066', 'Alarmas y Sensores', None),
                       ('MLC179831', 'Circuito de Cámaras', None),
                       ('MLC5713', 'Cámaras de Vigilancia', None),
                       ('MLC438578', 'Accesorios para Consolas', None),
                       ('MLC439527', 'Accesorios para PC Gaming', None),
                       ('MLC455245', 'Xbox Series X/S', VIDEO_GAME_CONSOLE),
                       ('MLC161962', 'Otros Xboxs', None),
                       ('MLC447778', 'Accesorios para PC Gaming', None),
                       ('MLC1655', 'Monitores y Accesorios', MONITOR), (
                           'MLC6263', 'Kits de Mouse y Teclado',
                           KEYBOARD_MOUSE_COMBO),
                       ('MLC1747', 'Accesorios para Vehículos', None),
                       ('MLC1071', 'Animales y Mascotas', None),
                       ('MLC1368', 'Arte, Librería y Cordonería', None),
                       ('MLC1384', 'Bebés', None),
                       ('MLC1246', 'Belleza y Cuidado Personal', None),
                       ('MLC1039', 'Cámaras y Accesorios', None),
                       ('MLC1276', 'Deportes y Fitness', None),
                       ('MLC3025', 'Libros, Revistas y Comics', None),
                       ('MLC3937', 'Relojes y Joyas', None),
                       ('MLC409431', 'Salud y Equipamiento Médico', None),
                       ('MLC174421', 'Pesas de Baño', None),
                       ('MLC66176', 'Termómetros', None),
                       ('MLC435370', 'Otros', None),
                       ('MLC3948', 'Relojes Murales', None),
                       ('MLC399230', 'Smartwatches', WEARABLE),
                       ('MLC1631', 'Adornos y Decoración del Hogar', None),
                       ('MLC1592', 'Cocina y Menaje', None),
                       ('MLC436380', 'Muebles para el Hogar', None),
                       ('MLC436246', 'Textiles de Hogar y Decoración', None),
                       ('MLC177171', 'Porteros Eléctricos', None),
                       ('MLC163740', 'Ampolletas', None),
                       ('MLC163822', 'Cintas LED', None),
                       ('MLC431414', 'Accesorios para TV', None),
                       ('MLC11830', 'Componentes Electrónicos', None),
                       ('MLC174349', 'Media Streaming', None),
                       ('MLC9239', 'Proyectores y Telones', None),
                       ('MLC409415', 'Asistentes Virtuales', None),
                       ('MLC1024', 'Equipos de DJ y Accesorios', None),
                       ('MLC440366', 'Micrófonos y Preamplificadores', None),
                       ('MLC1362', 'Camping, Caza y Pesca', None),
                       ('MLC410723', 'Monopatines y Scooters', None),
                       ('MLC1049', 'Accesorios para Cámaras', None),
                       ('MLC4660', 'Filmadoras y Cámaras de Acción', None),
                       ('MLC420011', 'Estudio e Iluminación', None),
                       ('MLC174272', 'Para Cámaras de Acción', None), (
                           'MLC430367', 'Tarjetas de Memoria y Lectores',
                           MEMORY_CARD),
                       ('MLC439596', 'Audífonos', HEADPHONES),
                       ('MLC448169', 'Controles para Gamers', None),
                       ('MLC187264', 'Sillas Gamer', GAMING_CHAIR),
                       ('MLC439597', 'Otros', None),
                       ('MLC159228', 'Para PlayStation', None),
                       ('MLC159227', 'Para Xbox', None),
                       (
                       'MLC116370', 'PS4 - PlayStation 4', VIDEO_GAME_CONSOLE),
                       (
                       'MLC455263', 'PS5 - PlayStation 5', VIDEO_GAME_CONSOLE),
                       ('MLC440985', 'Cables y Adaptadores', None),
                       ('MLC116375', 'Otros', None),
                       ('MLC430598', 'Almacenamiento', STORAGE_DRIVE),
                       ('MLC1691', 'Componentes de PC', None),
                       ('MLC1700', 'Conectividad y Redes', None),
                       ('MLC1657', 'Proyectores y Telones', None),
                       ('MLC1723', 'Software', None),
                       ('MLC159231', 'Estuches y Fundas', None),
                       ('MLC159245', 'Láminas Protectoras', None),
                       ('MLC3378', 'Parlantes para PC', STEREO_SYSTEM),
                       ('MLC1716', 'Mouse Pads', None),
                       ('MLC440873', 'Tabletas Digitalizadoras', TABLET),
                       ('MLC3377', 'Accesorios para Notebooks', None),
                       ('MLC54182', 'Bases Enfriadoras', None),
                       ('MLC9240', 'Cargadores y Fuentes', None),
                       ('MLC40749', 'Fundas', None),
                       ('MLC440858', 'Hubs USB', None),
                       ('MLC7223', 'Mochilas, Maletines y Fundas', None),
                       ('MLC3584', 'Otros', None),
                       ('MLC418042', 'Bases', None),
                       ('MLC21069', 'Monitores', MONITOR),
                       ('MLC440656', 'Adaptadores USB', None),
                       ('MLC430794', 'Cables de Red y Accesorios', None),
                       ('MLC430901', 'Routers', None),
                       ('MLC430788', 'Coolers y Ventiladores', None),
                       ('MLC430796', 'Discos y Accesorios', None),
                       ('MLC430916', 'Fuentes de Alimentación', POWER_SUPPLY),
                       ('MLC1696', 'Gabinetes y Soportes de PC',
                        COMPUTER_CASE), ('MLC1715', 'Cables', None),
                       ('MLC9729', 'Hubs USB', None),
                       ('MLC5895', 'Cables de Audio y Video', None),
                       ('MLC5877', 'Cables de Datos', None),
                       ('MLC1669', 'Discos y Accesorios', None),
                       ('MLC1673', 'Pen Drives', USB_FLASH_DRIVE),
                       ('MLC6777', 'Audífonos', HEADPHONES),
                       ('MLC440657', 'Controles para Gamers', None),
                       ('MLC447782', 'Sillas Gamer', GAMING_CHAIR),
                       ('MLC447784', 'Otros', None),
                       ('MLC417705', 'Otros', None),
                       ('MLC5107', 'Cables de Audio y Video', None),
                       ('MLC175456', 'Joysticks', None),
                       ('MLC7908', 'Memorias', MEMORY_CARD),
                       ('MLC58500', 'Soportes para Vehiculos', None),
                       ('MLC432439', 'Otros', None),
                       ('MLC420040', 'Fundas Cargadoras', None),
                       ('MLC157689', 'Otros', None),
                       ('MLC5702', 'Artículos de Bebé para Baños', None),
                       ('MLC1392', 'Juegos y Juguetes para Bebés', None),
                       ('MLC22867', 'Accesorios de Auto y Camioneta', None),
                       ('MLC3381', 'Audio para Vehículos', None),
                       ('MLC1058', 'Handies y Radiofrecuencia', None),
                       ('MLC5542', 'Manos Libres', None),
                       ('MLC1002', 'Televisores', TELEVISION),
                       ('MLC10177', 'Home Theater', STEREO_SYSTEM),
                       ('MLC1022', 'Parlantes y Subwoofers', STEREO_SYSTEM),
                       ('MLC2531', 'Climatización', AIR_CONDITIONER),
                       ('MLC1580', 'Hornos y Cocinas', OVEN),
                       ('MLC1578', 'Lavado', WASHING_MACHINE),
                       ('MLC1576', 'Refrigeración', REFRIGERATOR),
                       ('MLC9456', 'Refrigeradores', REFRIGERATOR),
                       ('MLC179816', 'Repuestos y Accesorios', None),
                       ('MLC4337', 'Aspiradoras', VACUUM_CLEANER),
                       ('MLC180993', 'Aspiradoras Robot', VACUUM_CLEANER),
                       ('MLC455108', 'Repuestos y Accesorios', None),
                       ('MLC178593', 'Lavadora-Secadoras', WASHING_MACHINE),
                       ('MLC174300', 'Lavavajillas', None),
                       ('MLC27590', 'Secadoras', WASHING_MACHINE),
                       ('MLC29800', 'Aires Acondicionados', AIR_CONDITIONER),
                       ('MLC176937', 'Repuestos y Accesorios', None),
                       ('MLC39109', 'Lápices y Uñetas', None),
                       ('MLC178483', 'Herramientas', None),
                       ('MLC1499', 'Industrias y Oficinas', None),
                       ('MLC1953', 'Otras Categorías', None),
                       ('MLC431994', 'Equipaje y Accesorios de Viaje', None),
                       ('MLC31406', 'Mochilas', None),
                       ('MLC435064', 'Tratamientos Respiratorios', None),
                       ('MLC179796', 'Humidificadores', None),
                       ('MLC179017', 'Purificadores de Aire', None),
                       ('MLC163741', 'Lámparas', None),
                       ('MLC1070', 'Otros', None),
                       ('MLC438287', 'Para Cocina', None),
                       ('MLC438286', 'Para Hogar', None),
                       ('MLC439831', 'Otros', None),
                       ('MLC440073', 'Artefactos para el Cabello', None),
                       ('MLC440072', 'Balanzas de Baño', None),
                       ('MLC1292', 'Ciclismo', None),
                       ('MLC440627', 'Pulsómetros y Cronómetros', None),
                       ('MLC179479', 'Monociclos Eléctricos', None),
                       ('MLC455434', 'Monopatines', None),
                       ('MLC178749', 'De Pie', None),
                       ('MLC455437', 'Eléctricos', None),
                       ('MLC163738', 'Cámaras', None),
                       ('MLC436831', 'Revelado y Laboratorio', None),
                       ('MLC17800', 'Antenas Wireless', None),
                       ('MLC11860', 'Parlantes', STEREO_SYSTEM),
                       ('MLC455192', 'Artefactos para el Cabello', None),
                       ('MLC417575', 'Barbería', None),
                       ('MLC1253', 'Cuidado de la Piel', None),
                       ('MLC393366', 'Higiene Personal', None),
                       ('MLC174815', 'Cepillos', None),
                       ('MLC447211', 'Cepillos Eléctricos', None),
                       ('MLC1720', 'UPS', 'Ups'),
                       ('MLC1722', 'Otros', None),
                       ('MLC157821', 'Ultrabooks', NOTEBOOK),
                       ('MLC440652', 'Switches', None),
                       ('MLC1694', 'Memorias RAM', RAM),
                       ('MLC1706', 'Tarjetas de Red', None),
                       ('MLC177923', 'Impresión', None),
                       ('MLC1676', 'Impresoras', PRINTER),
                       ('MLC2141', 'Insumos de Impresión', None),
                       ('MLC7415', 'Cartuchos de Tinta', None),
                       ('MLC10871', 'Tintas', None),
                       ('MLC3560', 'Toners', None),
                       ('MLC159250', 'Repuestos', None),
                       ('MLC191054', 'Micrófonos', MICROPHONE),
                       ('MLC159229', 'Para Nintendo', None),
                       ('MLC180910', 'Fuentes de Alimentación', POWER_SUPPLY),
                       ('MLC180896', 'Headsets', HEADPHONES),
                       ('MLC440885', 'Micrófonos', MICROPHONE),
                       ('MLC40780', 'Controles Remotos', None),
                       ('MLC3581', 'Docking Stations', None),
                       ('MLC26532', 'Maletines y Bolsos', None),
                       ('MLC26538', 'Mochilas', None),
                       ('MLC431333', 'Filtros de Privacidad', None),
                       ('MLC418043', 'Soportes', None),
                       ('MLC3553', 'Memorias Digitales', None),
                       ('MLC430373', 'Otros', None),
                       ('MLC181025', 'All In One', ALL_IN_ONE),
                       ('MLC1649', 'Computadores', None),
                       ('MLC178644', 'Mini PCs', None),
                       ('MLC175552', 'Soportes', None),
                       ('MLC440682', 'Repuestos para Notebooks', None),
                       ('MLC1014', 'Micro y Minicomponentes', STEREO_SYSTEM),
                       ('MLC438566', 'Consolas', VIDEO_GAME_CONSOLE),
                       ('MLC455247', 'Fundas y Estuches', None),
                       ('MLC455248', 'Otros', None),
                       ('MLC439072', 'Audio y Video para Gaming', None),
                       ('MLC180981', 'Cargadores', None),
                       ('MLC413744', 'Fundas para Controles', None),
                       ('MLC430797', 'Accesorios', None),
                       ('MLC1672', 'Discos Duros y SSDs', STORAGE_DRIVE),
                       ('MLC10190', 'Repuestos', None),
                       ('MLC9183', 'Sillas', None),
                       ('MLC412717', 'Sillas Tándem', None),
                       ('MLC58760', 'Cables de Audio y Video', None),
                       ('MLC36587', 'Otros Cables', None),
                       ('MLC108729', 'Soportes para Parlantes', None),
                       ('MLC5068', 'Baterías', None),
                       ('MLC159270', 'Videojuegos', None),
                       ('MLC1367', 'Antigüedades y Colecciones', None),
                       ('MLC1456', 'Lentes y Accesorios', None),
                       ('MLC174662', 'Llaveros', None),
                       ('MLC412056', 'Paraguas', None),
                       ('MLC66190', 'Lentes de Sol', None),
                       ('MLC66191', 'Ópticos', None),
                       ('MLC66170', 'Otros', None),
                       ('MLC433069', 'Juegos de Agua y Playa', None),
                       ('MLC455425', 'Juegos de Construcción', None),
                       ('MLC432988', 'Juegos de Mesa y Cartas', None),
                       ('MLC436967', 'Juegos de Salón', None),
                       ('MLC12037', 'Juguetes Antiestrés e Ingenio', None),
                       ('MLC432818', 'Juguetes de Oficios', None),
                       ('MLC432888', 'Muñecos y Muñecas', None),
                       ('MLC1166', 'Peluches', None),
                       ('MLC3422', 'Figuras de Acción', None),
                       ('MLC2968', 'Muñecas y Bebés', None),
                       ('MLC455651', 'Puzzles', None),
                       ('MLC455518', 'Trompos', None),
                       ('MLC437053', 'Cartas Coleccionables R.P.G.', None),
                       ('MLC1161', 'Juegos de Mesa', None),
                       ('MLC175991', 'Puzzles', None),
                       ('MLC432989', 'Otros', None),
                       ('MLC5541', 'Pilas y Cargadores', None),
                       ('MLC440349', 'Video', None),
                       ('MLC40673', 'Cargadores de Pilas', None),
                       ('MLC9828', 'Pilas', None),
                       ('MLC431488', 'Amplificadores y Receivers', None),
                       ('MLC172273', 'Pinballs y Arcade', None),
                       ('MLC2930', 'PS2 - PlayStation 2', VIDEO_GAME_CONSOLE),
                       ('MLC11623', 'PS3 - PlayStation 3', VIDEO_GAME_CONSOLE),
                       ('MLC455274', 'Cargadores para Controles', None),
                       ('MLC455268', 'Fundas para Controles', None),
                       ('MLC455266', 'Gamepads y Joysticks', None),
                       ('MLC180980', 'Controles', None),
                       ('MLC420068', 'Fuentes de Alimentación', POWER_SUPPLY),
                       ('MLC180986', 'Skins', None),
                       ('MLC439615', 'Controles y Joysticks', None),
                       ('MLC11625', 'Otros', None),
                       ('MLC4396', 'Game Boy Advance - GBA',
                        VIDEO_GAME_CONSOLE),
                       ('MLC2921', 'Game Cube', VIDEO_GAME_CONSOLE),
                       ('MLC178658', 'Nintendo Switch', VIDEO_GAME_CONSOLE),
                       ('MLC11223', 'Nintendo Wii', VIDEO_GAME_CONSOLE),
                       ('MLC116432', 'Nintendo Wii U', VIDEO_GAME_CONSOLE),
                       ('MLC161960', 'Otros Nintendos', None),
                       ('MLC190762', 'Fuentes de Alimentación', POWER_SUPPLY),
                       ('MLC413678', 'Fundas y Estuches', None),
                       ('MLC416556', 'Gamepads y Joysticks', None),
                       ('MLC413679', 'Protectores de Pantalla', None),
                       ('MLC178843', 'Otros', None),
                       ('MLC431792', 'Cables de Red', None),
                       ('MLC180937', 'Cuadernos', None),
                       ('MLC440143', 'Estuches de Lápices', None),
                       ('MLC177774', 'Enfriadores de Aire', None),
                       ('MLC183159', 'Estufas y Calefactores', None),
                       ('MLC161360', 'Ventiladores', None),
                       ('MLC162501', 'Planchas', None),
                       ('MLC162504', 'Hervidores', None),
                       ('MLC439832', 'Preparación de Alimentos', None),
                       ('MLC438297', 'Preparación de Bebidas', None),
                       ('MLC162503', 'Arroceras', None),
                       ('MLC440064', 'Batidoras', None),
                       ('MLC411071', 'Sartenes y Ollas Eléctricas', None),
                       ('MLC162507', 'Tostadoras', None),
                       ('MLC30852', 'Cocinas', None),
                       ('MLC174295', 'Extractores y Purificadores', None),
                       ('MLC30854', 'Hornos', OVEN),
                       ('MLC436300', 'Artículos de Vino y Coctelería', None),
                       ('MLC436280', 'Cocción y Horneado', OVEN),
                       ('MLC159273', 'Utensilios de Preparación', None),
                       ('MLC436289', 'Vajilla y Artículos de Servir', None),
                       ('MLC159287', 'Bandejas', None),
                       ('MLC1604', 'Cuchillería', None),
                       ('MLC159295', 'Cuchillos de Cocina', None),
                       ('MLC159294', 'Juegos de Cuchillería', None),
                       ('MLC455317', 'Coladores y Tendederos', None),
                       ('MLC455321', 'Medidores de Cocina', None),
                       ('MLC180827', 'Otros', None),
                       ('MLC159285', 'Baterías de Cocina', None),
                       ('MLC159283', 'Ollas', None),
                       ('MLC159284', 'Sartenes', None),
                       ('MLC440063', 'Balanzas de Cocina', None),
                       ('MLC438291', 'Máquinas para Postres', None),
                       ('MLC180819', 'Licuadoras', None),
                       ('MLC438298', 'Otros', None),
                       ('MLC4340', 'Cafeteras', None),
                       ('MLC30109', 'Otros', None),
                       ('MLC171531', 'Encimeras', None),
                       ('MLC385176', 'Calefonts y Termos', None),
                       ('MLC440149', 'Sistemas de Monitoreo', None),
                       ('MLC174413', 'Timbres', None),
                       ('MLC177173', 'Otros', None),
                       ('MLC439844', 'Dispensadores y Purificadores', None),
                       ('MLC455131', 'Cepillos', None),
                       ('MLC455118', 'Filtros', None),
                       ('MLC455113', 'Otros', None),
                       ('MLC1621', 'Jardín y Aire Libre', None),
                       ('MLC162500', 'Freidoras', None),
                       ('MLC174302', 'Hornos de Pan', None),
                       ('MLC30848', 'Microondas', OVEN),
                       ('MLC158419', 'Cavas de Vino', None),
                       ('MLC158426', 'Freezers', REFRIGERATOR),
                       ('MLC436298', 'Almacenamiento y Organización', None),
                       ('MLC1593', 'Vajilla', None),
                       ('MLC440224', 'Fuentes', None),
                       ('MLC179055', 'Jarras', None),
                       ('MLC30082', 'Juegos de Vajilla', None),
                       ('MLC436277', 'Afiladores', None),
                       ('MLC180832', 'Moldes', None),
                       ('MLC159275', 'Tablas para Picar', None),
                       ('MLC440222', 'Bandejas, Asaderas y Fuentes', None),
                       ('MLC440124', 'Baterías, Ollas y Sartenes', None),
                       ('MLC436281', 'Otros', None),
                       ('MLC440219', 'Vaporieras', None),
                       ('MLC1899', 'Otros', None),
                       ('MLC455059', 'Repuestos y Accesorios', None),
                       ('MLC30849', 'Otros', None),
                       ('MLC392350', 'Para Cocinas y Hornos', None),
                       ('MLC455060', 'Otros', None),
                       ('MLC392406', 'Calderas', None),
                       ('MLC29793', 'Chimeneas y Salamandras', None),
                       ('MLC431237', 'Calefonts', None),
                       ('MLC431238', 'Termos', None),
                       ('MLC1613', 'Baños', None),
                       ('MLC2521', 'Piscinas y Accesorios', None),
                       ('MLC455386', 'Spa Exterior', None),
                       ('MLC433511', 'Calentadores', None),
                       ('MLC440092', 'Limpieza y Mantenimiento', None),
                       ('MLC177072', 'Piscinas', None),
                       ('MLC30988', 'Otros', None),
                       ('MLC1590', 'Otros', None),
                       ('MLC1616', 'Accesorios para Baño', None),
                       ('MLC443824', 'Tinas', None),
                       ('MLC439847', 'Electricidad', None),
                       ('MLC180881', 'Mobiliario para Baños', None),
                       ('MLC440069', 'Jugueras', None),
                       ('MLC429556', 'Minipimers', None),
                       ('MLC174293', 'Parrillas Eléctricas', None),
                       ('MLC401945', 'Otros', None),
                       ('MLC162502', 'Sandwicheras', None),
                       ('MLC440067', 'Procesadores', None),
                       ('MLC179543', 'Waffleras', None),
                       ('MLC162505', 'Yogurteras', None),
                       ('MLC436275', 'Utensilios de Repostería', None),
                       ('MLC159296', 'Tenedores', None),
                       ('MLC455100', 'Para Aires Acondicionados', None),
                       ('MLC176940', 'Para Calefont y Termos', None),
                       ('MLC435273', 'Gasfitería', None),
                       ('MLC411938', 'Mobiliario para Cocinas', None),
                       ('MLC438290', 'Otros', None),
                       ('MLC440070', 'Exprimidores Eléctricos', None),
                       ('MLC175499', 'Mopas a Vapor', None),
                       ('MLC4222', 'Teclados', KEYBOARD),
                       ('MLC3709', 'Pantallas', None),
                       ('MLC159233', 'Pantallas', None),
                       ('MLC440859', 'Memorias RAM para Laptops', RAM),
                       ('MLC40779', 'Carcasas', None),
                       ('MLC26535', 'Otros', None),
                       ('MLC439836', 'Eléctricos', None),
                       ('MLC159342', 'Reproductor Blu-Ray', None),
                       ('MLC1588', 'Lámparas de Techo', None),
                       ('MLC418448', 'Teclados Físicos', KEYBOARD),
                       ('MLC455085', 'Otros', None),
                       ('MLC161249', 'Otros', None),
                       ('MLC385693', 'Filtros para Aires Ac.', None),
                       ('MLC392407', 'A Gas', None),
                       ('MLC161241', 'Eléctricas', None),
                       ('MLC159246', 'Carcasas', None),
                       ('MLC159234', 'Otros Accesorios', None),
                       ('MLC159251', 'Soportes', None),
                       ('MLC1695', 'Fuentes de Poder', POWER_SUPPLY),
                       ('MLC438144', 'A Combustión', None),
                       ('MLC440821', 'Gabinetes', COMPUTER_CASE),
                       ('MLC163820', 'Lámparas de Mesa', None),
                       ('MLC163742', 'Otras Lámparas', None),
                       ('MLC1586', 'Apliques de Pared', None),
                       ('MLC1585', 'Lámparas de Pie', None),
                       ('MLC183366', 'USB', None),
                       ('MLC39209', 'Para Auriculares', None),
                       ('MLC436012', 'Otros', None),
                       ('MLC6576', 'Chips', None),
                       ('MLC432444', 'Otros', None),
                       ('MLC429461', 'Docking Stations', None),
                       ('MLC3707', 'Discos Duros y SSDs', STORAGE_DRIVE),
                       ('MLC30850', 'Máquinas de Coser', None),
                       ('MLC1606', 'Balanzas de Cocina', None),
                       ('MLC174449', 'Parrillas Eléctricas', None),
                       ('MLC455114', 'Bolsas', None),
                       ('MLC174024', 'Máquinas para Helados', None),
                       ('MLC159269', 'Máquina para Pastas', None),
                       ('MLC162506', 'Vaporeras', None),
                       ('MLC375459', 'Woks', None),
                       ('MLC429383', 'Papel Mantequilla', None),
                       ('MLC436294', 'Pinzas', None),
                       ('MLC440220', 'Biferas', None),
                       ('MLC163539', 'Marcos para Fotos', None),
                       ('MLC1042', 'Cámaras Digitales', None),
                       ('MLC175537', 'Cámaras Análogas', None),
                       ('MLC175541', 'Estabilizadores para Cámaras', None),
                       ('MLC430419', 'Drones', None),
                       ('MLC179485', 'Drones', None),
                       ('MLC430383', 'Impresoras', PRINTER),
                       ('MLC437061', 'Trípodes para Cámaras', None),
                       ('MLC9776', 'Cargadores de Baterías', None),
                       ('MLC3542', 'Binoculares', None),
                       ('MLC174250', 'Micrófonos', MICROPHONE),
                       ('MLC70324', 'Para Cámaras Instantáneas', None),
                       ('MLC183303', 'Baterías', None),
                       ('MLC174273', 'Otros', None),
                       ('MLC436880', 'Álbumes de Fotos', None),
                       ('MLC440100', 'Bolsos', None),
                       ('MLC1045', 'Lentes', None),
                       ('MLC413541', 'Oculares', None),
                       ('MLC413487', 'Kits para Cámaras de Acción', None),
                       ('MLC440107', 'Otros', None),
                       ('MLC174279', 'Soportes y Bastones', None),
                       ('MLC174248', 'Carcasas', None),
                       ('MLC183305', 'Cargadores', None),
                       ('MLC3541', 'Telescopios', None),
                       ('MLC417788', 'Otros', None),
                       ('MLC183307', 'Otros', None),
                       ('MLC183313', 'Protectores de Hélices', None),
                       ('MLC431308', 'Convertidores de Zapatas', None),
                       ('MLC440101', 'Mochilas', None),
                       ('MLC70289', 'Fundas y Estuches', None),
                       ('MLC436887', 'Otros', None),
                       ('MLC3544', 'Otros', None),
                       ('MLC70326', 'Controles Remotos', None),
                       ('MLC9780', 'Baterías', None),
                       ('MLC440099', 'Para Cámaras de Video', None),
                       ('MLC430406', 'Baterías', None),
                       ('MLC3357', 'Otros', None),
                       ('MLC174249', 'Correas', None),
                       ('MLC9829', 'Otros', None),
                       ('MLC179487', 'Otros', None),
                       ('MLC440106', 'USB', None),
                       ('MLC183308', 'Cámaras', None),
                       ('MLC70325', 'Otros', None),
                       ('MLC179048', 'Iluminadores', None),
                       ('MLC1046', 'Filtros', None),
                       ('MLC414249', 'Kits para Estudio Fotográfico', None),
                       ('MLC183306', 'Controles', None),
                       ('MLC183309', 'Hélices', None),
                       ('MLC174247', 'Monitores', MONITOR),
                       ('MLC1914', 'Otros', None),
                       ('MLC179047', 'Flashes', None),
                       ('MLC70299', 'Grips', None),
                       ('MLC430411', 'Controles', None),
                       ('MLC436885', 'Tubos de Extensión', None),
                       ('MLC183302', 'Antenas', None),
                       ('MLC183310', 'Mochilas y Estuches', None),
                       ('MLC40697', 'Proyectores', None),
                       ('MLC18222', 'Soportes', None),
                       ('MLC440710', 'Cables Power', None),
                       ('MLC4075', 'Micrófonos', MICROPHONE),
                       ('MLC172568', 'Parlantes Portátiles', STEREO_SYSTEM),
                       ('MLC2876', 'Tornamesas', None),
                       ('MLC49668', 'Soportes', None),
                       ('MLC3698', 'Otros', None),
                       ('MLC455701', 'Reproductores Portátiles', None),
                       ('MLC174336', 'Conectores', None),
                       ('MLC60306', 'Digital', None),
                       ('MLC2854', 'Radios', None),
                       ('MLC40698', 'Telones', None),
                       ('MLC44388', 'Adaptadores', None),
                       ('MLC179474', 'Otros', None),
                       ('MLC175495', 'Interfaces de Audio', None),
                       ('MLC455686', 'Torres de Sonido', STEREO_SYSTEM),
                       ('MLC174313', 'Otros', None),
                       ('MLC174330', 'Sensores Inductivos', None),
                       ('MLC417360', 'Luces Led Profesionales', None),
                       ('MLC36529', 'Cables de Datos', None),
                       ('MLC1021', 'Sinto Amplificadores', None),
                       ('MLC174403', 'Monitores de Estudio', MONITOR),
                       ('MLC2675', 'Amplificadores', STEREO_SYSTEM),
                       ('MLC439802', 'Espumas Acústicas', None),
                       ('MLC430186', 'Para Media Streaming', None),
                       ('MLC44895', 'Lásers Profesionales', None),
                       ('MLC174561', 'Atriles', None),
                       ('MLC178457', 'Alisadores de Pelo', None),
                       ('MLC4597', 'Secadores de Pelo', None),
                       ('MLC5411', 'Máquinas para Cortar el Pelo', None),
                       ('MLC181012', 'Purificadores de Agua', None),
                       ('MLC178456', 'Alisadores', None),
                       ('MLC43660', 'Rizadores y Onduladores', None),
                       ('MLC433579', 'Filtros de Agua', None),
                       ('MLC11094', 'Micrófonos', MICROPHONE),
                       ('MLC440729', 'Reproductores de CD', None),
                       ('MLC429275', 'Correas', None),
                       ('MLC2907', 'Equipos Móviles', CELL),
                       ('MLC158420', 'Frigobares', REFRIGERATOR),
                       ('MLC2048', 'Joysticks', None),
                       ('MLC455246', 'Joysticks', None),
                       ('MLC448171', 'Joysticks', None),
                       ('MLC180982', 'Headsets', HEADPHONES),
                       ('MLC440875', 'Gamepads', None),
                       ('MLC440348', 'Para Otras Consolas', None),
                       ('MLC455264', 'Fuentes de Alimentación', POWER_SUPPLY),
                       ('MLC455415', 'Cámaras', None),
                       ('MLC46509', 'Volantes', None),
                       ('MLC58405', 'Gamepads y Joysticks', None),
                       ('MLC439660', 'Cables y Adaptadores', None),
                       ('MLC416554', 'Gamepads y Joysticks', None),
                       ('MLC11964', 'Otros', None),
                       ('MLC116433', 'Otros', None),
                       ('MLC440647', 'Otros', None),
                       ('MLC174376', 'Walkman', None)]

    @classmethod
    def categories(cls):
        # We are hardcoding the categories for now to slowly input ML SKUs
        # over time
        return [
            CELL,
            NOTEBOOK,
            STEREO_SYSTEM,
            KEYBOARD,
            MOUSE,
            WEARABLE,
            TABLET,
            REFRIGERATOR,
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            VIDEO_GAME_CONSOLE,
            MONITOR,
            MEMORY_CARD,
            GAMING_CHAIR,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            WASHING_MACHINE,
            TELEVISION,

        ]
        # return [i for i in set(cls.categories_name.values()) if i]

    @classmethod
    def get_products(cls, session, category=None, query_code=None,
                     seller_id=None, official_store_id=None,
                     only_official_stores=True):
        offset = 0
        product_urls = []

        base_url = 'https://api.mercadolibre.com/sites/MLC/search?' \
                   'limit=50'

        if query_code:
            base_url += '&category=' + query_code

        if seller_id:
            base_url += '&seller_id=' + str(seller_id)

        if official_store_id:
            base_url += '&official_store_id=' + str(official_store_id)
        elif only_official_stores:
            base_url += '&official_store=all'

        while True:
            if offset > 1000:
                raise Exception('Page overflow')

            url = '{}&offset={}'.format(base_url, offset)
            response = session.get(url)
            product_containers = json.loads(response.text)
            if not product_containers['results']:
                if offset == 0:
                    logging.warning('Empty category: ' + category or 'Unkown')
                break

            for container in product_containers['results']:
                # If during normal search (that is, without an associated
                # seller_id or official_store_id) we find a product with
                # an unknown category, skip it.
                # Implementations such as ML LG and ML Samsung may
                # find these cases too, but we need to consider all of their
                # products always.
                unknown_category = False
                if not seller_id and not official_store_id:
                    for category_code, category_ml, real_category in \
                            cls.categories_code:
                        if category_code == container['category_id'] and \
                                real_category != category:
                            unknown_category = True
                            break
                if unknown_category:
                    continue

                product_url = container['permalink'] + '?'

                if seller_id:
                    product_url += 'pdp_filters=seller_id:{}'.format(seller_id)
                elif only_official_stores:
                    product_official_store_id = container['official_store_id']
                    product_url += 'pdp_filters=official_store:{}'. \
                        format(product_official_store_id)

                product_urls.append(product_url)

            offset += 50
        return product_urls

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        print(category)
        session = session_with_proxy(extra_args)
        product_urls = []
        for category_code, category_name, real_category in cls.categories_code:
            if real_category == category:
                product_urls.extend(
                    cls.get_products(session, category, category_code))
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        new_mode_data = re.search(
            r'window.__PRELOADED_STATE__ =([\S\s]+?);\n', page_source)
        data = json.loads(new_mode_data.groups()[0])

        for entry in data['initialState']['components'].get('head', []):
            if entry['id'] == 'item_status_message' and 'PAUSADA' in \
                    entry['body']['text'].upper():
                return []

        if url.startswith('https://articulo.mercadolibre.cl/'):
            return cls.retrieve_type2_products(session, url, soup,
                                               category, data)
        elif url.startswith('https://www.mercadolibre.cl/'):
            return cls.retrieve_type3_products(data, session, category)
        else:
            # Another scraper with embedded ML pages
            try:
                return cls.retrieve_type2_products(session, url, soup,
                                                   category, data)
            except Exception:
                return cls.retrieve_type3_products(data, session, category)

    @classmethod
    def retrieve_type3_products(cls, data, session, category):
        print('Type3')
        variations = set()
        pickers = data['initialState']['components'].get('variations', {}).get(
            'pickers', None)

        official_store_or_seller_filter = data['initialState'].get(
            'filters', None)

        if pickers:
            for picker in pickers:
                for product in picker['products']:
                    variations.add(product['id'])
        else:
            variations.add(data['initialState']['id'])

        products = []

        for variation in variations:
            sku = variation
            endpoint = 'https://api.mercadolibre.com/products/' \
                       '{}'.format(variation)

            if official_store_or_seller_filter:
                endpoint += '?{}'.format(
                    official_store_or_seller_filter.replace(':', '='))

            variation_data = json.loads(session.get(endpoint).text)

            if variation_data.get('status', None) != 'active':
                continue

            box_winner = variation_data['buy_box_winner']

            if not box_winner:
                continue

            name = variation_data['name']
            url = variation_data['permalink']

            if official_store_or_seller_filter:
                url += '?pdp_filters={}'.format(
                    official_store_or_seller_filter)

            price = Decimal(box_winner['price'])
            stock = int(box_winner['available_quantity'])

            seller_endpoint = 'https://api.mercadolibre.com/users/' \
                '{}'.format(box_winner['seller_id'])
            seller_info = json.loads(session.get(seller_endpoint).text)
            seller = seller_info['nickname']
            picture_urls = [p['url'] for p in variation_data['pictures']]

            products.append(Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                seller=seller,
                picture_urls=picture_urls,
                description='Type3'
            ))

        return products

    @classmethod
    def retrieve_type2_products(cls, session, url, soup, category, data):
        print('Type2')
        seller = data['initialState']['components']['track'][
            'analytics_event']['custom_dimensions'][
            'customDimensions']['officialStore']
        sku = data['initialState']['id']
        base_name = data['initialState']['components'][
            'short_description'][0]['title']
        price = Decimal(data['initialState']['schema'][0][
            'offers']['price'])

        picker = None
        for x in data['initialState']['components']['short_description']:
            if x['id'] == 'variations' and 'pickers' in x:
                if len(x['pickers']) == 1:
                    picker = x['pickers'][0]
                else:
                    # I'm not sure how to handle multiple pickers
                    # https://articulo.mercadolibre.cl/MLC-547289939-
                    # samartband-huawei-band-4-pro-_JM
                    picker = None

        products = []

        if picker:
            picker_id = picker['id']
            for variation in picker['products']:
                color_name = variation['label']['text']
                name = '{} ({})'.format(base_name, color_name)
                color_id = variation['attribute_id']

                if '?' in url:
                    separator = '&'
                else:
                    separator = '?'

                variation_url = '{}{}attributes={}:{}'.format(url, separator,
                                                              picker_id,
                                                              color_id)
                res = session.get(variation_url)
                key_match = re.search(r'variation=(\d+)', res.url)

                if key_match:
                    key = key_match.groups()[0]
                    variation_url = '{}?variation={}'.format(url, key)
                else:
                    key = variation['id']

                products.append(Product(
                    name,
                    cls.__name__,
                    category,
                    variation_url,
                    url,
                    key,
                    -1,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    seller=seller,
                    description='Type2'
                ))
        else:
            picture_urls = [x['data-zoom'] for x in
                            soup.findAll('img', 'ui-pdp-image')[1::2]
                            if 'data-zoom' in x.attrs]
            products.append(Product(
                base_name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                -1,
                price,
                price,
                'CLP',
                sku=sku,
                seller=seller,
                picture_urls=picture_urls,
                description='Type2'
            ))
        return products

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        offset = 0
        result = []

        while offset < threshold:
            endpoint = 'https://api.mercadolibre.com/sites/MLC/search?q={}' \
                       '&offset={}&official_store=all'.format(
                           urllib.parse.quote(keyword), offset)
            json_results = json.loads(session.get(endpoint).text)
            for product_entry in json_results['results']:
                result.append(product_entry['permalink'])
                if len(result) >= threshold:
                    break
            offset += 50

        return result
