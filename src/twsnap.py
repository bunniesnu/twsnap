from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep as sl
from PIL import Image
from .webdriver import get_driver
from os.path import exists
from os import remove
from .utils import is_valid_tweet_url, get_tweet_file_name

class Twsnap:
    driver = None
    driver_path = None
    gui = False
    mode = 3
    night_mode = 0
    wait_time = 5
    chrome_opts = []
    lang = None
    test = False
    show_parent_tweets = False
    parent_tweets_limit = 0
    show_mentions_count = 0
    overwrite = False
    radius = 15
    scale = 3.0
    cookies = None
    width = 700

    hide_link_previews = False
    hide_photos = False
    hide_videos = False
    hide_gifs = False
    hide_quotes = False

    def __init__(self, driver_path: str = None, gui: bool = False, mode: int = 3, hide_link_previews: bool = False, hide_photos: bool = False, hide_videos: bool = False, hide_gifs: bool = False, hide_quotes: bool = False, scale: float = 1.0, width: int = 700):
        self.gui = gui
        self.mode = mode
        self.hide_link_previews = hide_link_previews
        self.hide_photos = hide_photos
        self.hide_videos = hide_videos
        self.hide_gifs = hide_gifs
        self.hide_quotes = hide_quotes
        self.scale = scale
        self.driver_path = driver_path
        self.width = width
    
    async def screenshot(self, url: str, night_mode = None, overwrite = True, path = './output.png', scale=None):
        if is_valid_tweet_url(url) is False:
            raise Exception("Invalid tweet url")

        if not isinstance(path, str) or len(path) == 0:
            path = get_tweet_file_name(url)

        if exists(path):
            if (self.overwrite if overwrite is None else overwrite) is False:
                raise Exception("File already exists")
            else:
                remove(path)

        url = is_valid_tweet_url(url)
        if self.lang:
            url += "?lang=" + self.lang

        # radius = self.radius if radius is None else radius
        scale = self.scale if scale is None else scale
        driver = get_driver(self.chrome_opts, self.driver_path, gui=self.gui, scale=scale)
        if driver is None:
            raise Exception("webdriver cannot be initialized")
        try:
            driver.get(url)

            # Apply cookies
            driver.add_cookie({"name": "night_mode", "value": str(self.night_mode if night_mode is None else night_mode)})
            driver.get(url)

            driver.execute_script(f'document.body.style.zoom=\'{100*self.scale}%\'')
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "(//ancestor::article)/.."))
                )
            finally:
                print()
            
            self.__hide_global_items(driver)
            main = driver.find_element(By.XPATH, "(//ancestor::article)/..")
            main_articles = main.find_elements(By.XPATH, "(//ancestor::article)/div/div/div[3]/div")
            if self.mode == 0:
                for i in range(len(main_articles)-1):
                    if len(main_articles[i+1].get_attribute("innerHTML"))==0:
                        driver.execute_script("""
                        arguments[0].setAttribute('style','padding-bottom:15px;')
                        """, main_articles[i])
                        break

            # Mode
            self.__code_main_footer_items_new(main,self.mode)
            self.__hide_media(main, self.hide_link_previews, self.hide_photos, self.hide_videos, self.hide_gifs, self.hide_quotes)
            self.set_width(driver=driver, element=main, width=self.width)

            border_element = driver.find_element(By.XPATH, '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[1]')
            self.border_remove(driver, border_element)


            driver.execute_script("window.scrollTo(0, 0);")


            self.upscale_profile_pic(driver)

            sl(2)

            x, y, width, height = driver.execute_script("var rect = arguments[0].getBoundingClientRect(); return [rect.x, rect.y, rect.width, rect.height];", main)
            driver.save_screenshot(path)
            im = Image.open(path)
            im = im.crop((x*self.scale, y*self.scale, (x + width)*self.scale, (y + height)*self.scale))
            im.save(path)
            im.close()

            driver.quit()
        except Exception as err:
            driver.quit()
            raise err
        return path
            

    def __hide_global_items(self, driver):
        HIDE_ITEMS_XPATH = [
            '/html/body/div/div/div/div[1]',
            '/html/body/div/div/div/div[2]/header', '/html/body/div/div/div/div[2]/main/div/div/div/div/div/div[1]',
            ".//ancestor::div[@data-testid = 'tweetButtonInline']/../../../../../../../../../../..",
            '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[2]'
        ]
        for item in HIDE_ITEMS_XPATH:
            try:
                element = driver.find_element(By.XPATH, item)
                driver.execute_script("""
                arguments[0].style.display="none";
                """, element)
            except:
                continue

    def hide_all_media(self):
        self.hide_link_previews = True
        self.hide_photos = True
        self.hide_videos = True
        self.hide_gifs = True
        self.hide_quotes = True  

    def hide_media(self, link_previews=None, photos=None, videos=None, gifs=None, quotes=None):
        if link_previews is not None: self.hide_link_previews = link_previews
        if photos is not None: self.hide_photos = photos
        if videos is not None: self.hide_videos = videos
        if gifs is not None: self.hide_gifs = gifs
        if quotes is not None: self.hide_quotes = quotes
    
    def __hide_media(self, element, link_previews, photo, video, gif, quote):
        LINKPREVIEW_XPATH = ".//ancestor::div[@data-testid = 'card.layoutLarge.media']/ancestor::div[contains(@id, 'id__')][1]"
        MEDIA_XPATH = ".//ancestor::div[@data-testid = 'tweetPhoto']/ancestor::div[contains(@id, 'id__')]/div[1]"
        QUOTE_XPATH = ".//ancestor::div[contains(@class, 'r-desppf')]/ancestor::div[contains(@id, 'id__')][1]"
        media_elements = element.find_elements(By.XPATH, MEDIA_XPATH)
        if link_previews is True:
            link_preview_elements = element.find_elements(By.XPATH, LINKPREVIEW_XPATH)
            for link_preview_element in link_preview_elements:
                element.parent.execute_script("""
                arguments[0].style.display="none";
                """, link_preview_element)
        if quote is True:
            quote_elements = element.find_elements(By.XPATH, QUOTE_XPATH)
            for quote_element in quote_elements:
                element.parent.execute_script("""
                arguments[0].style.display="none";
                """, quote_element)
        if len(media_elements) > 0:
            for el in media_elements:
                if video is True:
                    sel = el.find_elements(By.XPATH, ".//video[contains(@src, 'blob:')]")
                    if len(sel) > 0:
                        element.parent.execute_script("""
                        arguments[0].style.display="none";
                        """, el)
                        continue
                    sel = el.find_elements(By.XPATH, ".//source[contains(@src, 'blob:')]")
                    if len(sel) > 0:
                        element.parent.execute_script("""
                        arguments[0].style.display="none";
                        """, el)
                        continue
                if gif is True:
                    sel = el.find_elements(By.XPATH, ".//video[not(contains(@src, 'blob:'))]")
                    if len(sel) > 0:
                        element.parent.execute_script("""
                        arguments[0].style.display="none";
                        """, el)
                        continue
                if gif is True:
                    sel = el.find_elements(By.XPATH, ".//video[not(contains(@src, 'blob:'))]")
                    if len(sel) > 0:
                        element.parent.execute_script("""
                        arguments[0].style.display="none";
                        """, el)
                        continue
                if photo is True:
                    sel = el.find_elements(By.XPATH, ".//div[contains(@data-testid, 'videoPlayer')]")
                    if len(sel) == 0:
                        element.parent.execute_script("""
                        arguments[0].style.display="none";
                        """, el)
                        continue

    def __code_main_footer_items_new(self, element, mode):
        XPATHS = [
            ".//ancestor::time/ancestor::a[contains(@aria-describedby, 'id__')]", # 0 time
            ".//div[@role = 'group'][contains(@id, 'id__')]", # 1 action buttons
            ".//div[@role = 'group'][not(contains(@id, 'id__'))]", # 2 tweet rt/like/bookmark counts
            ".//div[contains(@data-testid, 'caret')]", # 3 tweet caret button
            "((//ancestor::span)/..)[contains(@role, 'button')]", # 4 translate button
            ".//div[contains(@data-testid, 'caret')]/../../../../..", # 5 tweet caret button / subscribe-follow button
            ".//ancestor::time/../../..//span[contains(text(), '·')]/..", # 6 separator between time and views
            ".//ancestor::time/../../../div[3]", # 7 views
            ".//ancestor::time/../../../../..", # 8 time & views outer
            ".//ancestor::time/../../../../../..", # 9 time & views outer (with margin)
            ".//div[@role = 'group'][contains(@id, 'id__')]/../../../div[contains(@class, 'r-j5o65s')]", # 10 border line
        ]

        newInfoMode = True
        try:
            if len(element.find_elements(By.XPATH, ".//div[@role = 'separator']")) > 0:
                newInfoMode = False
        except:
            pass
        
        hides = []
        if mode == 0: # hide everything
            hides = [0,1,2,3,4,5,6,7,9]
            if newInfoMode is True: hides.append(10)
        elif mode == 1: # show tweet rt/likes
            hides = [0,3,4,5,6]
            if newInfoMode is False: hides.append(1)
        elif mode == 2: # show tweet rt/likes & timestasmp
            hides = [3,4,5]
            if newInfoMode is False: hides.append(1)
        elif mode == 3: # show everything
            hides = [3,4,5]
        elif mode == 4: # show timestamp
            hides = [1,2,3,4,5,6,7]

        viewsVisible = False
        try:
            if len(element.find_elements(By.XPATH, "((//ancestor::time)/..)[contains(@aria-describedby, 'id__')]/../../div")) > 1:
                viewsVisible = True
        except:
            pass

        # if time hidden and views not there, hide outer (to clear gaps)
        if (mode != 0) and (0 in hides) and (viewsVisible is False):
            hides.append(8)

        for i in hides:
            els = element.find_elements(By.XPATH, XPATHS[i])
            if len(els) > 0:
                for el in els:
                    element.parent.execute_script("""
                    arguments[0].style.display="none";
                    """, el)
        
        brdr = element.find_elements(By.XPATH, XPATHS[2])
        if len(brdr) == 1:
            element.parent.execute_script("""
            arguments[0].style.borderBottom="none";
            """, brdr[0])
    
    def upscale_profile_pic(self, driver):
        profile_img = driver.find_element(By.XPATH, '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/section/div/div/div/div/div/article/div/div/div[2]/div[1]/div/div/div/div/div[2]/div/div[2]/div/a/div[3]/div/div[2]/div')
        profile_img_img = profile_img.find_element(By.TAG_NAME, "img")
        profile_img_img_link = "_".join(profile_img_img.get_attribute('src').split('_')[:2])+"_400x400.jpg"
        driver.execute_script("arguments[0].style.display='none';", profile_img.find_element(By.TAG_NAME, "div"))
        driver.execute_script(f"arguments[0].setAttribute('src', '{profile_img_img_link}'); arguments[0].setAttribute('class','');", profile_img_img)

    def border_remove(self, driver, element):
        driver.execute_script(f"arguments[0].setAttribute('class','{element.get_attribute('class').replace(' r-13l2t4g','')}')",element)

    def set_width(self, driver, element, width):
        driver.execute_script(f"arguments[0].style.width='{width}px'", element)

    def set_chromedriver_path(self, chromedriver):
        self.driver_path = chromedriver