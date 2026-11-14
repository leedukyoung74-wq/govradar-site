# English Wikipedia article for each country's capital (or a defining city/landscape), used to pick one free-licence hero photo.
CAP = {
"AF":"Kabul","AL":"Tirana","DZ":"Algiers","AD":"Andorra la Vella","AO":"Luanda","AG":"St. John's, Antigua and Barbuda","AR":"Buenos Aires","AM":"Yerevan","AU":"Sydney","AT":"Vienna",
"AZ":"Baku","BS":"Nassau, Bahamas","BH":"Manama","BD":"Dhaka","BB":"Bridgetown","BY":"Minsk","BE":"Brussels","BZ":"Belize City","BJ":"Cotonou","BT":"Thimphu",
"BO":"La Paz","BA":"Sarajevo","BW":"Gaborone","BR":"Brasília","BN":"Bandar Seri Begawan","BG":"Sofia","BF":"Ouagadougou","BI":"Bujumbura","CV":"Praia","KH":"Phnom Penh",
"CM":"Yaoundé","CA":"Ottawa","CF":"Bangui","TD":"N'Djamena","CL":"Santiago","CN":"Beijing","CO":"Bogotá","KM":"Moroni, Comoros","CG":"Brazzaville","CD":"Kinshasa",
"CR":"San José, Costa Rica","CI":"Abidjan","HR":"Zagreb","CU":"Havana","CY":"Nicosia","CZ":"Prague","DK":"Copenhagen","DJ":"Djibouti (city)","DM":"Roseau","DO":"Santo Domingo",
"EC":"Quito","EG":"Cairo","SV":"San Salvador","GQ":"Malabo","ER":"Asmara","EE":"Tallinn","SZ":"Mbabane","ET":"Addis Ababa","FJ":"Suva","FI":"Helsinki",
"FR":"Paris","GA":"Libreville","GM":"Banjul","GE":"Tbilisi","DE":"Berlin","GH":"Accra","GR":"Athens","GD":"St. George's, Grenada","GT":"Guatemala City","GN":"Conakry",
"GW":"Bissau","GY":"Georgetown, Guyana","HT":"Port-au-Prince","HN":"Tegucigalpa","HU":"Budapest","IS":"Reykjavík","IN":"New Delhi","ID":"Jakarta","IR":"Tehran","IQ":"Baghdad",
"IE":"Dublin","IL":"Tel Aviv","IT":"Rome","JM":"Kingston, Jamaica","JP":"Tokyo","JO":"Amman","KZ":"Astana","KE":"Nairobi","KI":"South Tarawa","KP":"Pyongyang",
"KR":"Seoul","KW":"Kuwait City","KG":"Bishkek","LA":"Vientiane","LV":"Riga","LB":"Beirut","LS":"Maseru","LR":"Monrovia","LY":"Tripoli, Libya","LI":"Vaduz",
"LT":"Vilnius","LU":"Luxembourg City","MG":"Antananarivo","MW":"Lilongwe","MY":"Kuala Lumpur","MV":"Malé","ML":"Bamako","MT":"Valletta","MH":"Majuro","MR":"Nouakchott",
"MU":"Port Louis","MX":"Mexico City","FM":"Palikir","MD":"Chișinău","MC":"Monaco","MN":"Ulaanbaatar","ME":"Podgorica","MA":"Rabat","MZ":"Maputo","MM":"Yangon",
"NA":"Windhoek","NR":"Nauru","NP":"Kathmandu","NL":"Amsterdam","NZ":"Wellington","NI":"Managua","NE":"Niamey","NG":"Lagos","MK":"Skopje","NO":"Oslo",
"OM":"Muscat","PK":"Islamabad","PW":"Koror","PA":"Panama City","PG":"Port Moresby","PY":"Asunción","PE":"Lima","PH":"Manila","PL":"Warsaw","PT":"Lisbon",
"QA":"Doha","RO":"Bucharest","RU":"Moscow","RW":"Kigali","KN":"Basseterre","LC":"Castries","VC":"Kingstown","WS":"Apia","SM":"City of San Marino","ST":"São Tomé",
"SA":"Riyadh","SN":"Dakar","RS":"Belgrade","SC":"Victoria, Seychelles","SL":"Freetown","SG":"Singapore","SK":"Bratislava","SI":"Ljubljana","SB":"Honiara","SO":"Mogadishu",
"ZA":"Cape Town","SS":"Juba","ES":"Madrid","LK":"Colombo","SD":"Khartoum","SR":"Paramaribo","SE":"Stockholm","CH":"Bern","SY":"Damascus","TJ":"Dushanbe",
"TZ":"Dar es Salaam","TH":"Bangkok","TL":"Dili","TG":"Lomé","TO":"Nukuʻalofa","TT":"Port of Spain","TN":"Tunis","TR":"Istanbul","TM":"Ashgabat","TV":"Funafuti",
"UG":"Kampala","UA":"Kyiv","AE":"Dubai","GB":"London","US":"Washington, D.C.","UY":"Montevideo","UZ":"Tashkent","VU":"Port Vila","VE":"Caracas","VN":"Hanoi",
"YE":"Sanaa","ZM":"Lusaka","ZW":"Harare",
# autonomous / special regions
"PH-BARMM":"Cotabato City","IQ-KRI":"Erbil","TZ-ZAN":"Stone Town","ID-AC":"Banda Aceh","ID-PP":"Jayapura","PG-NSB":"Buka, Papua New Guinea","MY-SBH":"Kota Kinabalu",
"MY-SWK":"Kuching","CN-HK":"Hong Kong","CN-MO":"Macau","DK-GL":"Nuuk","DK-FO":"Tórshavn","FI-AX":"Mariehamn","PT-20":"Ponta Delgada","PT-30":"Funchal",
"ES-PV":"Bilbao","ES-CT":"Barcelona","GB-SCT":"Edinburgh","GB-WLS":"Cardiff","GB-NIR":"Belfast","FR-NC":"Nouméa","US-PR":"San Juan, Puerto Rico","SO-SL":"Hargeisa",
}

# second round: landmark / skyline articles for places whose capital lead photo was a montage, too small or missing
ALT = {
"AF":"Darul Aman Palace","BF":"Bobo-Dioulasso","CM":"Douala","CR":"National Theatre of Costa Rica","JM":"Blue Mountains (Jamaica)","MG":"Avenue of the Baobabs",
"MU":"Le Morne Brabant","MM":"Shwedagon Pagoda","NI":"Granada, Nicaragua","PG":"Rabaul","VC":"Saint Vincent (Antilles)","SC":"Anse Source d'Argent",
"TT":"Maracas Bay","PG-NSB":"Bougainville Island","MY-SWK":"Kuching Waterfront","GB-WLS":"Cardiff Castle","SO-SL":"Laas Geel","CN-HK":"Victoria Harbour",
"CN-MO":"Ruins of St. Paul's","SG":"Marina Bay, Singapore","ES-PV":"Guggenheim Museum Bilbao","FI-AX":"Åland","BZ":"Great Blue Hole","CF":"Ubangi River",
"ER":"Fiat Tagliero Building","MC":"Monte Carlo","MZ":"Island of Mozambique","NR":"Anibare Bay","SR":"Saint Peter and Paul Cathedral, Paramaribo",
}

# third round for the last places without a usable free photo
ALT3 = {"BZ":"Xunantunich","CF":"Dzanga-Sangha Special Reserve","CN-HK":"Victoria Peak","FI-AX":"Kastelholm Castle","JM":"Dunn's River Falls",
"PG-NSB":"Mount Bagana","SC":"Mahé, Seychelles","SO-SL":"Berbera","TT":"Queen's Park Savannah"}
