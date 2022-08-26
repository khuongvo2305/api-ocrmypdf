from asyncore import read
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Set
from uuid import UUID

from pydantic import BaseModel

from api.settings import config
from api.tools import special_win_wslpath

import json
import requests
import re
class Lang(str, Enum):
    eng = "eng"
    # fra = "fra"
    # dan = "dan"
    # nld = "nld"
    # fin = "fin"
    # deu = "deu"
    # hun = "hun"
    # ita = "ita"
    # nor = "nor"
    # por = "por"
    # ron = "ron"
    # rus = "rus"
    # spa = "spa"
    # swe = "swe"
    # tur = "tur"
    vie = "vie"


class Document(BaseModel):
    pid: UUID
    lang: Set[Lang]
    status: str
    input: Path
    output: Path
    output_json: Path
    output_txt: Path
    output_related_document: Path
    result: Optional[str] = None
    code: Optional[int] = None
    created: datetime
    processing: Optional[datetime] = None
    expire: datetime
    finished: Optional[datetime] = None

    def ocr(self, wsl: bool = False):
        self.status = "processing"
        self.processing = datetime.now()
        self.save_state()

        # Hack for user using OCRmyPDF inside WSL (Windows)
        output_txt_path = (
            special_win_wslpath(self.output_txt)
            if wsl
            else str(self.output_txt.absolute())
        )
        input_path = (
            special_win_wslpath(self.input) if wsl else str(self.input.absolute())
        )
        output_path = (
            special_win_wslpath(self.output) if wsl else str(self.output.absolute())
        )
        try:
            output = subprocess.check_output(
                " ".join(
                    [
                        config.base_command_ocr,
                        config.base_command_option,
                        f"-l {'+'.join([l.value for l in self.lang])}",
                        f"--sidecar {output_txt_path}",
                        input_path,
                        output_path,
                    ]
                ),
                stderr=subprocess.STDOUT,
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            self.status = "error"
            self.code = e.returncode
            self.result = e.output.strip()
            self.finished = datetime.now()
        else:
            self.status = "done"
            self.code = 0
            self.result = str(output).strip()
            self.finished = datetime.now()
        finally:
            self.save_state()
            self.get_related_api()

    def save_state(self):
        with open(self.output_json, "w") as ff:
            ff.write(self.json())

    def get_related_api(self):
        result = []
        with open(str(self.output_txt.absolute()), "r",encoding="utf-8", errors='backslashreplace') as ff:
            sidecarss = ff.readlines()
            for sidecars in sidecarss:
                if sidecars != "":
                    sidecars = re.sub(""," ",sidecars)
                    sidecars = re.sub(r"/\s\s+/g"," ",sidecars)
                    url = config.related_document_api  
                    payload = json.dumps({
                    "query": sidecars
                    })
                    response = requests.request("POST", url, json={
                    "query": sidecars
                    })
                    with open(self.output_related_document, "w") as fp:
                        # try:
                        res = json.loads(response.text)
                        for item in res:
                            if len(item["output"])>0:
                                print(item)
                                result.append(item)
                        
                        # except:
                            
                        #     print("Error %s"%response.text)
                            # result.extend([{"output":[],"Error":response.text, "sent_failed":sidecars}])
       
        with open(self.output_related_document, "w") as f:
            f.write(json.dumps(result))
            # json.dump(result,self.output_related_document)
    def delete_all_files(self):
        if self.input.exists():
            self.input.unlink()
        if self.output.exists():
            self.output.unlink()
        if self.output_json.exists():
            self.output_json.unlink()
        if self.output_related_document.exists():
            self.output_related_document.unlink()
        if self.output_txt.exists():
            self.output_txt.unlink()
