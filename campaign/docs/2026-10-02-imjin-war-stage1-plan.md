# 임진왜란 캠페인 1단계 구현 계획

> **에이전트 작업자용:** 필수 하위 스킬 — `subagent-driven-development`(권장) 또는 `executing-plans`로 작업 단위마다 진행한다. 단계는 체크박스(`- [ ]`)로 추적한다.

**목표:** Unciv에서 "새 게임 → 시나리오 → 임진왜란 1장"을 고르면 조선으로 고정된 채 프롤로그부터 옥포·사천 해전을 거쳐 승리 또는 패배까지 플레이할 수 있게 한다.

**구조:** 엔진에는 본가에 PR할 수 있는 작은 패치 두 개(시나리오 플레이어 문명 고정, 이벤트 화자·초상화)만 넣는다. 캠페인 내용은 전부 확장 모드 `Imjin War 1592`(JSON)로 만든다. 시나리오 세이브는 손으로 만들지 않고 Kotlin 빌드 도구가 문자 지도와 배치 코드에서 생성한다.

**기술 스택:** Kotlin, libGDX(헤드리스), Gradle 9.4.1, JUnit 4.13.2, JDK 21(Android Studio JBR), Python 3 + Pillow(맵 생성·아트 후처리), 코덱스 짭 MCP(GPT 이미지)

**설계 문서:** `campaign/docs/2026-10-02-imjin-war-campaign-design.md` — 실행자는 이 계획과 설계 문서를 같이 읽는다.

## 전역 제약

- 저장소 루트: `C:\c_e\testgame\Unciv`, 브랜치 `imjin-campaign`. 아래 경로는 모두 저장소 루트 기준이다.
- JDK: PATH에 `java`가 없다. Gradle 명령마다 PowerShell에서 앞에 `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr';`를 붙인다.
- 테스트 실행: `.\gradlew.bat :tests:test --tests "<클래스 또는 패턴>"` (테스트 작업 디렉터리는 `android/assets`).
- 커밋 작성자는 저장소 로컬 설정(`fff1045-git`)을 그대로 쓴다. 커밋 메시지 끝에 빈 줄 하나 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`를 붙인다.
- 엔진 패치(작업 1, 2)의 커밋에는 `campaign/`이나 `tests/build.gradle.kts` 변경을 섞지 않는다. 나중에 본가 PR 브랜치로 그대로 옮기기 위해서다.
- 엔진 패치는 새 필드·새 동작을 쓰지 않는 기존 모드와 시나리오의 동작을 바꾸지 않는다. 주변 코드 스타일(4칸 들여쓰기, KDoc 주석)을 따른다.
- 기본 룰셋(`android/assets/jsons/`)은 수정하지 않는다.
- 모드 폴더 이름 = 룰셋 이름 = `Imjin War 1592`. 내부 ID(문명, 유닛, 자원, 건물, 이벤트, 승리 조건)는 영어이고, 화면 이름은 모드의 `Korean.properties`로 붙인다. 이벤트 본문·대사·선택지 문구는 한국어로 직접 쓴다.
- 이벤트·선택지·승리 문구 같은 한국어 문장에 대괄호 `[]`와 중괄호 `{}`를 쓰지 않는다. Unciv 번역기가 자리표시자로 해석한다.
- 이미지 생성은 코덱스 짭 MCP의 GPT 이미지 도구로 한다(`codex-jjap-mcp` 스킬). Scenario MCP는 쓰지 않는다.

## 설계 대비 변경 사항

계획을 쓰면서 코드를 확인한 결과, 설계 문서와 다르게 가는 부분이다. 설계 문서도 같이 고쳐 두었다.

| 항목 | 설계 문서 | 이 계획 | 이유 |
|---|---|---|---|
| 패배 처리 | 우회안 검증 후 필요하면 엔진 장치 | 엔진 수정 없음. 일본 전용 승리 조건 `Japanese Conquest`의 이정표가 `[[Defeat Flag] resource of [Human player] Civilizations]`를 센다 | 다른 문명의 자원을 세는 countable(`Countables.kt:398`)이 이미 있다 |
| 이순신 유닛 | 위대한 제독 기반 장수 유닛 | 원거리 전투 함선(지휘선) + 주변 함선 강화 | 위대한 제독은 민간 유닛이라 호위가 죽으면 포획된다. 전사 판정이 애매하다 |
| 프롤로그 표시 | 1장 시작 이벤트 | 빌드 도구가 세이브의 팝업 대기열에 첫 이벤트를 넣는다 | 시나리오를 불러온 첫 턴에는 턴 시작 발동이 돌지 않는다 |
| 해역 표시 | (미정) | 이미지 없는 지형 특성 `Okpo Waters`, `Sacheon Waters`를 연안 타일에 깐다 | 지형 특성 이름이 tileFilter로 바로 쓰이고, 이미지가 없으면 그리지 않는다(`TileLayerTerrain.kt:23-30`) |
| 연도 | (미정) | 모드 게임 속도 `Imjin War`: 1592.33년 시작, 턴당 0.01년(약 3.65일) | 상단 바에 기원전 4000년이 뜨지 않게 |
| 빌드 도구 위치 | 실행 방식 미정 | `campaign/tools/src`를 tests 소스셋에 추가하고 Gradle 태스크 `:tests:buildScenarios` | tests 모듈에 헤드리스 libGDX와 테스트 러너가 이미 있다 |
| 이억기 대기 선택의 대가 | 적 함대도 늘어남 | 판옥선 2척을 얻는 대신 제한 턴이 40에서 36으로 줄어든다 | 조선 쪽 플래그만으로 구현할 수 있다 |

## 파일 구조

**엔진 (본가 PR 대상)**

| 파일 | 변경 | 책임 |
|---|---|---|
| `core/src/com/unciv/logic/GameInfo.kt` | 수정 | `GameInfoPreview.getScenarioPlayers()` 추가: 시나리오 세이브에서 플레이어 목록을 만든다 |
| `core/src/com/unciv/ui/screens/newgamescreen/ScenarioSelectTable.kt` | 수정 | 위 함수 사용 |
| `core/src/com/unciv/ui/screens/newgamescreen/MapOptionsTable.kt` | 수정 | 시나리오 선택 전에 표를 잠근다 |
| `core/src/com/unciv/ui/screens/newgamescreen/PlayerPickerTable.kt` | 수정 | 잠긴 표에서 고정 문명을 되돌리거나 지우지 않고, AI/사람 토글을 막는다 |
| `docs/Modders/Scenarios.md` | 수정 | 플레이어 문명 지정 방법 문서화 |
| `tests/src/com/unciv/logic/ScenarioPlayersTest.kt` | 생성 | 패치 1 테스트 |
| `core/src/com/unciv/models/ruleset/Event.kt` | 수정 | `speaker`, `portrait` 필드 |
| `core/src/com/unciv/ui/screens/worldscreen/RenderEvent.kt` | 수정 | 화자 줄 그리기 |
| `core/src/com/unciv/models/translations/TranslationFileWriter.kt` | 수정 | `Event.portrait` 번역 제외 |
| `docs/Modders/schemas/Events.schema.json`, `docs/Modders/Mod-file-structure/5-Miscellaneous-JSON-files.md` | 수정 | 새 필드 문서화 |
| `tests/src/com/unciv/uniques/EventSpeakerTest.kt` | 생성 | 패치 2 테스트 |

**캠페인 (포크 전용)**

| 파일 | 책임 |
|---|---|
| `campaign/maps/ch1-south-sea.txt` | **이미 있음.** 1장 맵(48×24 문자 지도) |
| `campaign/tools/mapgen/south_sea.py` | **이미 있음.** 위 맵을 경위도 해안선에서 다시 만드는 스크립트 |
| `.gitignore` | **이미 수정함.** Unciv의 `maps/`, `scenarios/` 규칙이 경로 제한 없이 걸려 있어서, 끝에 `!/campaign/**/maps/`, `!/campaign/**/scenarios/` 예외를 추가했다 |
| `campaign/Imjin War 1592/jsons/*.json` | 모드 룰셋 |
| `campaign/Imjin War 1592/jsons/translations/Korean.properties` | 한국어 표시명 |
| `campaign/Imjin War 1592/ExtraImages/`, `Images/` | 아트 |
| `campaign/Imjin War 1592/scenarios/Imjin War 1 - Guard the Sea` | 생성된 1장 세이브 |
| `campaign/tools/src/com/unciv/campaign/CampaignEnvironment.kt` | 헤드리스 초기화, 모드 로드 |
| `campaign/tools/src/com/unciv/campaign/AsciiMap.kt` | 문자 지도 → TileMap |
| `campaign/tools/src/com/unciv/campaign/ScenarioBuilder.kt` | 시나리오 GameInfo 조립과 저장 |
| `campaign/tools/src/com/unciv/campaign/Chapter1.kt` | 1장 배치 |
| `campaign/tools/src/com/unciv/campaign/BuildScenarios.kt` | `main()`: 세이브 파일 생성 |
| `campaign/tools/src/com/unciv/campaign/*Test.kt` | 모드·도구·1장 테스트 |
| `campaign/tools/art/postprocess.py` | 생성 이미지를 Unciv 규격으로 변환 |
| `tests/build.gradle.kts` | tests 소스셋에 `../campaign/tools/src` 추가, `buildScenarios` 태스크 |

---

### 작업 1: 엔진 패치 1 — 시나리오의 플레이어 문명 고정

**Files:**
- Modify: `core/src/com/unciv/logic/GameInfo.kt` (클래스 `GameInfoPreview`, 882-912행)
- Modify: `core/src/com/unciv/ui/screens/newgamescreen/ScenarioSelectTable.kt:51-52`
- Modify: `core/src/com/unciv/ui/screens/newgamescreen/MapOptionsTable.kt:52-57`
- Modify: `core/src/com/unciv/ui/screens/newgamescreen/PlayerPickerTable.kt:97, 160-167, 202-213`
- Modify: `docs/Modders/Scenarios.md:23-31`
- Test: `tests/src/com/unciv/logic/ScenarioPlayersTest.kt`

**Interfaces:**
- Produces: `fun GameInfoPreview.getScenarioPlayers(): ArrayList<Player>` — 작업 4, 5의 테스트가 쓴다.

**배경:** 지금은 `ScenarioSelectTable.selectScenario()`가 세이브의 `gameParameters.players`를 그대로 복사한다. 그 목록에는 보통 "Random" 슬롯만 있어서, `NewGameScreen.startNewGame()`(317-341행)이 사람 플레이어를 무작위 주요 문명에 배정한다. 게다가 `MapOptionsTable`이 표를 잠그기 전에 `selectScenario()`가 `playerPickerTable.update()`를 부르고, `reassignRemovedModReferences()`가 "Will not be chosen for new games" 문명을 Random으로 되돌린다.

- [ ] **Step 0: 빌드 환경 확인**

Run:
```powershell
$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.uniques.EventCircularTriggersTest"
```
Expected: `BUILD SUCCESSFUL`. 첫 실행은 의존성을 내려받느라 몇 분 걸린다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/src/com/unciv/logic/ScenarioPlayersTest.kt`:
```kotlin
package com.unciv.logic

import com.unciv.Constants
import com.unciv.logic.civilization.CivilizationInfoPreview
import com.unciv.logic.civilization.PlayerType
import com.unciv.models.metadata.Player
import org.junit.Assert.assertEquals
import org.junit.Test

class ScenarioPlayersTest {
    private fun preview(players: List<Player>, vararg civs: Pair<String, PlayerType>) = GameInfoPreview().apply {
        gameParameters.players = ArrayList(players)
        civilizations = civs.map { (id, type) ->
            CivilizationInfoPreview().apply { civID = id; playerType = type }
        }.toMutableList()
    }

    @Test
    fun civSavedAsHumanTakesARandomSlot() {
        val preview = preview(
            listOf(Player(Constants.spectator, PlayerType.Human), Player(), Player()),
            Constants.spectator to PlayerType.Human, "Joseon" to PlayerType.Human, "Toyotomi" to PlayerType.AI
        )
        val players = preview.getScenarioPlayers()
        assertEquals(listOf("Joseon", Constants.random), players.map { it.chosenCiv })
        assertEquals(listOf(PlayerType.Human, PlayerType.AI), players.map { it.playerType })
    }

    @Test
    fun scenarioWithoutSavedHumanKeepsTheOldBehaviour() {
        val preview = preview(
            listOf(Player(Constants.spectator, PlayerType.Human), Player(), Player()),
            Constants.spectator to PlayerType.Human, "Joseon" to PlayerType.AI, "Toyotomi" to PlayerType.AI
        )
        val players = preview.getScenarioPlayers()
        assertEquals(listOf(Constants.random, Constants.random), players.map { it.chosenCiv })
        assertEquals(listOf(PlayerType.AI, PlayerType.AI), players.map { it.playerType })
    }

    @Test
    fun explicitEntryForTheHumanCivBecomesHuman() {
        val preview = preview(
            listOf(Player("Joseon", PlayerType.AI), Player("Toyotomi", PlayerType.AI)),
            "Joseon" to PlayerType.Human, "Toyotomi" to PlayerType.AI
        )
        val players = preview.getScenarioPlayers()
        assertEquals(listOf("Joseon", "Toyotomi"), players.map { it.chosenCiv })
        assertEquals(listOf(PlayerType.Human, PlayerType.AI), players.map { it.playerType })
    }

    @Test
    fun addsASlotWhenNoneIsFree() {
        val preview = preview(listOf(Player("Toyotomi", PlayerType.AI)), "Joseon" to PlayerType.Human, "Toyotomi" to PlayerType.AI)
        val players = preview.getScenarioPlayers()
        assertEquals(listOf("Toyotomi", "Joseon"), players.map { it.chosenCiv })
        assertEquals(PlayerType.Human, players[1].playerType)
    }

    @Test
    fun leavesTheCachedPreviewUntouched() {
        val preview = preview(listOf(Player(Constants.spectator, PlayerType.Human), Player()), "Joseon" to PlayerType.Human)
        preview.getScenarioPlayers()
        assertEquals(listOf(Constants.spectator, Constants.random), preview.gameParameters.players.map { it.chosenCiv })
    }
}
```

- [ ] **Step 2: 실패 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.logic.ScenarioPlayersTest"`
Expected: 컴파일 실패, `Unresolved reference 'getScenarioPlayers'`.

- [ ] **Step 3: `getScenarioPlayers()` 구현**

`core/src/com/unciv/logic/GameInfo.kt`의 import 목록에 `import com.unciv.models.metadata.Player`를 추가한다(`com.unciv.logic.civilization.*`는 이미 있어서 `PlayerType`은 따로 필요 없다). `GameInfoPreview`의 `getPlayerCiv` 아래(907행 다음)에 추가:
```kotlin
    /** The players to offer when this save is started as a scenario: the saved player list without the Spectator,
     *  where every civ saved as Human is fixed to that civ. It takes over its own entry if there is one,
     *  else the first "Random" entry, else a new entry.
     *  Returns copies, so the new game screen can edit them without touching this (cached) preview. */
    fun getScenarioPlayers(): ArrayList<Player> {
        val players = gameParameters.players
            .filter { it.chosenCiv != Constants.spectator }
            .mapTo(ArrayList()) { Player(it.chosenCiv, it.playerType, it.playerId) }
        for (civ in civilizations) {
            if (!civ.isPlayerCivilization() || civ.civID == Constants.spectator) continue
            val slot = players.firstOrNull { it.chosenCiv == civ.civID }
                ?: players.firstOrNull { it.chosenCiv == Constants.random }
                ?: Player().also { players.add(it) }
            slot.chosenCiv = civ.civID
            slot.playerType = PlayerType.Human
        }
        return players
    }
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.logic.ScenarioPlayersTest"`
Expected: 5개 테스트 PASS.

- [ ] **Step 5: 새 게임 화면에 연결**

`ScenarioSelectTable.kt` 51-52행
```kotlin
        newGameScreen.gameSetupInfo.gameParameters.players = preload.gameParameters.players
            .apply { removeAll { it.chosenCiv == Constants.spectator } }
```
을 다음으로 바꾼다:
```kotlin
        newGameScreen.gameSetupInfo.gameParameters.players = preload.getScenarioPlayers()
```
그 뒤 `Constants` import가 더 쓰이지 않으면 지운다.

`MapOptionsTable.kt` 52-57행에서 잠금을 선택보다 먼저 한다:
```kotlin
                MapGeneratedMainType.scenario -> {
                    mapParameters.name = ""
                    mapTypeSpecificTable.add(scenarioOptionsTable)
                    // Lock first: selectScenario updates the player table, which must already treat the scenario's players as fixed
                    newGameScreen.lockTables()
                    scenarioOptionsTable.selectScenario()
                }
```

`PlayerPickerTable.kt`:
1. 97행 `if (gameParameters.players.size > newRulesetPlayableCivs)`를 `if (!locked && gameParameters.players.size > newRulesetPlayableCivs)`로 바꾼다. 시나리오의 문명은 "새 게임에서 선택 불가"여도 지우지 않는다.
2. `reassignRemovedModReferences()` 본문 첫 줄에 추가:
```kotlin
        // A scenario's players are fixed by the scenario file, including nations hidden from new games
        if (locked) return
```
3. `updatePlayerTypeButtonEnabled()`의 `when`에서 첫 분기 앞에 추가:
```kotlin
                // A scenario fixed this nation to its player type
                locked && player.chosenCiv != Constants.random -> false
```
4. 63행의 `locked` KDoc을 현재 쓰임에 맞게 고친다:
```kotlin
    /** Locks the player table for scenarios: no adding/removing players, no nation changes, and nations fixed by the scenario keep their player type. */
```

- [ ] **Step 6: 문서 갱신**

`docs/Modders/Scenarios.md`의 "To create a scenario" 목록에서 "Save the game..." 줄 앞에 추가:
```markdown
- To fix which nation the player plays, set it to human before saving: `civ setplayertype <nation> human`. Nations left as AI are played by the AI.
```
"When loading a scenario"의 27-29행(`- Humans will be assigned ...`부터 `Contact us ...`까지)을 다음으로 바꾼다:
```markdown
- Nations that were human when the scenario was saved (other than the Spectator) are fixed to human players, and the new game screen does not let you change them.
  If none were, humans are assigned from the choices on the new game screen: only the number of humans can be chosen, and your player will be assigned a random scenario civilization.
```

- [ ] **Step 7: 컴파일과 관련 테스트 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.logic.*"`
Expected: `BUILD SUCCESSFUL`, 실패 0.

- [ ] **Step 8: 커밋**

```powershell
git add core/src/com/unciv/logic/GameInfo.kt core/src/com/unciv/ui/screens/newgamescreen/ScenarioSelectTable.kt core/src/com/unciv/ui/screens/newgamescreen/MapOptionsTable.kt core/src/com/unciv/ui/screens/newgamescreen/PlayerPickerTable.kt docs/Modders/Scenarios.md tests/src/com/unciv/logic/ScenarioPlayersTest.kt
git commit -m "Scenarios: keep the nations saved as human as fixed human players" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### 작업 2: 엔진 패치 2 — 이벤트의 화자와 초상화

**Files:**
- Modify: `core/src/com/unciv/models/ruleset/Event.kt:10-30`
- Modify: `core/src/com/unciv/ui/screens/worldscreen/RenderEvent.kt:44-64`
- Modify: `core/src/com/unciv/models/translations/TranslationFileWriter.kt:741`
- Modify: `docs/Modders/schemas/Events.schema.json:15-18`
- Modify: `docs/Modders/Mod-file-structure/5-Miscellaneous-JSON-files.md:134-143`
- Test: `tests/src/com/unciv/uniques/EventSpeakerTest.kt`

**Interfaces:**
- Produces: `Event.speaker: String`, `Event.portrait: String` (기본값 `""`). 작업 6의 Events.json이 쓴다. `portrait`는 아틀라스 이미지 이름 또는 모드 `ExtraImages` 안의 파일 이름(확장자 생략 가능)이다. 예: `"Portraits/Yi Sun-sin"` → `ExtraImages/Portraits/Yi Sun-sin.png`.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/src/com/unciv/uniques/EventSpeakerTest.kt`:
```kotlin
package com.unciv.uniques

import com.unciv.json.json
import com.unciv.models.ruleset.Event
import org.junit.Assert.assertEquals
import org.junit.Test

class EventSpeakerTest {
    private fun parse(text: String): Event = json().fromJson(Array<Event>::class.java, text).single()

    @Test
    fun speakerAndPortraitAreRead() {
        val event = parse("""[{"name":"Okpo","text":"Hold fast","speaker":"Yi Sun-sin","portrait":"Portraits/Yi Sun-sin","choices":[{"text":"Attack"}]}]""")
        assertEquals("Yi Sun-sin", event.speaker)
        assertEquals("Portraits/Yi Sun-sin", event.portrait)
    }

    @Test
    fun eventsWithoutASpeakerKeepEmptyDefaults() {
        val event = parse("""[{"name":"Plain","text":"Nothing to see","choices":[{"text":"OK"}]}]""")
        assertEquals("", event.speaker)
        assertEquals("", event.portrait)
    }
}
```

- [ ] **Step 2: 실패 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.uniques.EventSpeakerTest"`
Expected: 컴파일 실패, `Unresolved reference 'speaker'`.

- [ ] **Step 3: 필드 추가**

`Event.kt`의 `var text = ""` 아래에 추가:
```kotlin
    /** Who is speaking, shown with [portrait] above [text]. Optional. */
    var speaker = ""
    /** Image shown beside [speaker]: an atlas image name, or a file in a mod's ExtraImages folder
     *  (extension optional) - found the same way as civilopediaText's extraImage. Optional. */
    var portrait = ""
```

- [ ] **Step 4: 테스트 통과 확인**

Run: 위와 같은 명령. Expected: 2개 PASS.

- [ ] **Step 5: 팝업에 화자 줄 그리기**

`RenderEvent.kt` import에 추가:
```kotlin
import com.badlogic.gdx.scenes.scene2d.ui.Image
import com.unciv.Constants
import com.unciv.ui.components.extensions.toLabel
import com.unciv.ui.images.ImageGetter
```
`init`의 `if (isValid) {` 바로 안, `if (event.text.isNotEmpty())` 앞에 추가:
```kotlin
            if (event.speaker.isNotEmpty() || event.portrait.isNotEmpty())
                add(getSpeakerRow(event)).row()
```
`addChoice` 앞에 추가:
```kotlin
    private fun getSpeakerRow(event: Event): Table {
        val row = Table()
        val portrait = getPortrait(event.portrait)
        if (portrait != null) {
            // Fit into a square of portraitSize, keeping the aspect ratio
            val scale = portraitSize / maxOf(portrait.width, portrait.height)
            row.add(portrait).size(portrait.width * scale, portrait.height * scale).padRight(10f)
        }
        if (event.speaker.isNotEmpty())
            row.add(event.speaker.toLabel(fontSize = Constants.headingFontSize, hideIcons = true))
        return row
    }

    /** Same lookup as civilopediaText's extraImage: atlas first, then ExtraImages of the mods and the base game */
    private fun getPortrait(name: String): Image? {
        if (name.isEmpty()) return null
        if (ImageGetter.imageExists(name)) return ImageGetter.getImage(name)
        val file = ImageGetter.findExternalImage(name) ?: return null
        return ImageGetter.getExternalImage(file)
    }
```
클래스 끝(`openCivilopedia` 아래)에 추가:
```kotlin
    private companion object {
        const val portraitSize = 128f
    }
```

- [ ] **Step 6: 번역 제외와 문서**

`TranslationFileWriter.kt` 741행 `"keyShortcut",` 다음 줄에 `"Event.portrait",`를 추가한다. 화자 이름(`speaker`)은 번역 대상으로 남긴다.

`Events.schema.json`의 `"text"` 속성 블록(15-18행) 뒤에 추가:
```json
      "speaker": {
        "type": "string",
        "description": "Who is speaking. Shown above the text, beside the portrait."
      },
      "portrait": {
        "type": "string",
        "description": "Image shown beside the speaker: an atlas image name, or a file in the mod's ExtraImages folder (extension optional), like civilopediaText's extraImage."
      },
```

`5-Miscellaneous-JSON-files.md`의 Events 표에서 `text` 줄(137행) 아래에 두 줄을 추가한다:
```markdown
| speaker         | String                              | None     | Who is speaking - shown above the text, beside the portrait                                                              |
| portrait        | String                              | None     | Image beside the speaker: atlas image name, or a file in the mod's ExtraImages folder, like civilopediaText's extraImage |
```
143행(`You can use text and/or civilopediaText...`) 아래에 추가:
```markdown
For a conversation, chain events: give each line its own event with a speaker and portrait, and a single choice that triggers the next line with "Triggers a [event] event".
```

- [ ] **Step 7: 전체 테스트**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test`
Expected: `BUILD SUCCESSFUL`. 실패가 있으면 이 작업의 변경과 관련 있는지 확인한다. 이 브랜치 시작 시점부터 실패하던 테스트라면 `git stash`로 변경을 빼고 같은 테스트를 돌려 확인한 뒤 결과를 보고한다.

- [ ] **Step 8: 커밋**

```powershell
git add core/src/com/unciv/models/ruleset/Event.kt core/src/com/unciv/ui/screens/worldscreen/RenderEvent.kt core/src/com/unciv/models/translations/TranslationFileWriter.kt docs/Modders/schemas/Events.schema.json docs/Modders/Mod-file-structure/5-Miscellaneous-JSON-files.md tests/src/com/unciv/uniques/EventSpeakerTest.kt
git commit -m "Events: optional speaker and portrait shown above the event text" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### 작업 3: 모드 룰셋 골격

**Files:**
- Modify: `tests/build.gradle.kts:44-48`
- Create: `campaign/tools/src/com/unciv/campaign/CampaignEnvironment.kt`
- Create: `campaign/Imjin War 1592/jsons/ModOptions.json`, `Speeds.json`, `Nations.json`, `Units.json`, `TileResources.json`, `Terrains.json`, `Buildings.json`, `VictoryTypes.json`, `translations/Korean.properties`
- Test: `campaign/tools/src/com/unciv/campaign/ImjinModTest.kt`

**Interfaces:**
- Produces:
  - `object CampaignEnvironment { const val MOD_NAME = "Imjin War 1592"; const val CAMPAIGN_FOLDER = "../../campaign"; const val MOD_FOLDER = "../../campaign/Imjin War 1592"; fun init() }`. 경로는 작업 디렉터리 `android/assets` 기준이다.
  - 룰셋 ID(작업 4~6이 쓴다):
    - 문명: `Joseon`, `Toyotomi`, `Ming`
    - 유닛: `Panokseon`, `Turtle Ship`(조선 전용으로 재정의), `Yi Sun-sin`, `Atakebune`, `Sekibune`, `Japanese Transport`
    - 자원(비축 플래그): `Naval Readiness`, `Popular Support`, `Court Unity`, `Ships Sunk`, `Defeat Flag`, `Okpo Speech Seen`, `Sacheon Event Seen`, `Waited For Yi Eok-gi`
    - 지형 특성: `Okpo Waters`, `Sacheon Waters`
    - 건물: `Chapter 1 HQ`, `Japanese Command Ch1`
    - 승리 조건: `Imjin Chapter 1`, `Japanese Conquest`
    - 게임 속도: `Imjin War`

- [ ] **Step 1: tests 소스셋에 캠페인 도구 추가**

`tests/build.gradle.kts`의 `sourceSets` 블록을 다음으로 바꾼다:
```kotlin
sourceSets {
    test {
        java.srcDir("src")
        // Imjin War campaign dev tools and their tests (fork only, not part of upstream Unciv)
        java.srcDir("../campaign/tools/src")
    }
}
```

- [ ] **Step 2: 환경 초기화 코드 작성**

`campaign/tools/src/com/unciv/campaign/CampaignEnvironment.kt`:
```kotlin
package com.unciv.campaign

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.backends.headless.HeadlessFiles
import com.badlogic.gdx.files.FileHandle
import com.unciv.UncivGame
import com.unciv.models.metadata.GameSettings
import com.unciv.models.ruleset.Ruleset
import com.unciv.models.ruleset.RulesetCache

/** Headless setup shared by the scenario builder and the campaign tests.
 *  Paths are relative to android/assets, the working directory of `desktop:run`, the tests and `:tests:buildScenarios`. */
object CampaignEnvironment {
    const val MOD_NAME = "Imjin War 1592"
    const val CAMPAIGN_FOLDER = "../../campaign"
    const val MOD_FOLDER = "$CAMPAIGN_FOLDER/$MOD_NAME"

    fun init() {
        if (Gdx.files == null) Gdx.files = HeadlessFiles()
        UncivGame.Current = UncivGame()
        UncivGame.Current.settings = GameSettings().apply {
            musicVolume = 0f
            soundEffectsVolume = 0f
            citySoundsVolume = 0f
            voicesVolume = 0f
        }
        if (RulesetCache.isEmpty()) RulesetCache.loadRulesets(consoleMode = true, noMods = true)
        loadMod()
    }

    /** Loads the mod straight from campaign/, so neither the builder nor the tests depend on the android/assets/mods junction */
    fun loadMod(): Ruleset {
        val folder = FileHandle(MOD_FOLDER)
        require(folder.child("jsons").isDirectory) { "Mod folder not found: ${folder.file().absolutePath}" }
        val mod = Ruleset().apply {
            name = MOD_NAME
            load(folder.child("jsons"))
            folderLocation = folder
        }
        RulesetCache[MOD_NAME] = mod
        return mod
    }
}
```

- [ ] **Step 3: 실패하는 테스트 작성**

`campaign/tools/src/com/unciv/campaign/ImjinModTest.kt`:
```kotlin
package com.unciv.campaign

import com.unciv.models.metadata.BaseRuleset
import com.unciv.models.ruleset.RulesetCache
import com.unciv.testing.GdxTestRunner
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(GdxTestRunner::class)
class ImjinModTest {
    @Before
    fun setUp() = CampaignEnvironment.init()

    @Test
    fun modDefinesTheCampaignObjects() {
        val mod = RulesetCache[CampaignEnvironment.MOD_NAME]!!
        for (nation in listOf("Joseon", "Toyotomi", "Ming")) assertTrue(nation, nation in mod.nations)
        for (unit in listOf("Panokseon", "Turtle Ship", "Yi Sun-sin", "Atakebune", "Sekibune", "Japanese Transport"))
            assertTrue(unit, unit in mod.units)
        for (flag in listOf("Naval Readiness", "Popular Support", "Court Unity", "Ships Sunk", "Defeat Flag",
                "Okpo Speech Seen", "Sacheon Event Seen", "Waited For Yi Eok-gi"))
            assertTrue(flag, flag in mod.tileResources)
        for (terrain in listOf("Okpo Waters", "Sacheon Waters")) assertTrue(terrain, terrain in mod.terrains)
        for (building in listOf("Chapter 1 HQ", "Japanese Command Ch1")) assertTrue(building, building in mod.buildings)
        for (victory in listOf("Imjin Chapter 1", "Japanese Conquest")) assertTrue(victory, victory in mod.victories)
        assertTrue("Imjin War" in mod.speeds)
    }

    @Test
    fun modPassesTheModChecker() {
        val ownErrors = RulesetCache[CampaignEnvironment.MOD_NAME]!!.getErrorList()
        assertFalse(ownErrors.getErrorText(true), ownErrors.isWarnUser())
        val (_, combinedErrors) = RulesetCache.checkCombinedModLinks(linkedSetOf(CampaignEnvironment.MOD_NAME), BaseRuleset.Civ_V_GnK.fullName)
        assertFalse(combinedErrors.getErrorText(true), combinedErrors.isWarnUser())
    }
}
```

- [ ] **Step 4: 실패 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.campaign.ImjinModTest"`
Expected: FAIL, `Mod folder not found`.

- [ ] **Step 5: 모드 JSON 작성**

`campaign/Imjin War 1592/jsons/ModOptions.json`:
```json
{
    "author": "fff1045-git",
    "topics": ["unciv-mod-rulesets", "unciv-mod-expansion"],
    "uniques": []
}
```

`Speeds.json`:
```json
[
    {
        "name": "Imjin War",
        "startYear": 1592.33,
        "turns": [ {"yearsPerTurn": 0.01, "untilTurn": 400} ],
        "uniques": ["Will not be displayed in Civilopedia"]
    }
]
```

`Nations.json`:
```json
[
    {
        "name": "Joseon",
        "leaderName": "Seonjo",
        "adjective": ["Joseon"],
        "outerColor": [27, 33, 96],
        "innerColor": [235, 195, 70],
        "uniques": ["Will not be chosen for new games"],
        "cities": ["Yeosu", "Suncheon", "Jinju", "Hanseong", "Pyeongyang", "Uiju", "Jeonju", "Gwangju", "Haenam", "Tongyeong"],
        "introduction": "과인은 조선의 임금이오. 이 나라의 산하와 바다를 지키는 것이 과인의 소임이오.",
        "neutralHello": "어서 오시오.",
        "hateHello": "또 그대인가.",
        "attacked": "무도한 자들이로다. 온 나라의 백성이 일어나 그대들을 막으리라.",
        "defeated": "종묘와 사직을 지키지 못하였구나.",
        "declaringWar": "더는 참을 수 없소. 조선의 군사가 그대들을 칠 것이오.",
        "tradeRequest": "서로 이로운 일을 의논해 봅시다."
    },
    {
        "name": "Toyotomi",
        "leaderName": "Toyotomi Hideyoshi",
        "adjective": ["Japanese"],
        "outerColor": [245, 245, 245],
        "innerColor": [150, 20, 20],
        "uniques": ["Will not be chosen for new games"],
        "cities": ["Busan", "Gimhae", "Ungcheon", "Seosaengpo", "Nagoya", "Osaka"],
        "introduction": "나는 히데요시다. 명으로 가는 길을 빌려 달라 했을 뿐이거늘.",
        "neutralHello": "무슨 일인가.",
        "hateHello": "조선의 사신인가.",
        "attacked": "감히 나에게 칼을 겨누는가.",
        "defeated": "이슬로 왔다가 이슬로 사라지는구나.",
        "declaringWar": "길을 비켜라. 대명으로 가는 길이다.",
        "tradeRequest": "거래를 하자는 것인가."
    },
    {
        "name": "Ming",
        "leaderName": "Wanli Emperor",
        "adjective": ["Ming"],
        "outerColor": [250, 210, 40],
        "innerColor": [160, 20, 20],
        "uniques": ["Will not be chosen for new games"],
        "cities": ["Beijing", "Liaoyang", "Nanjing"],
        "introduction": "짐은 대명의 천자다. 번국의 일을 어찌 모른 체하겠는가.",
        "neutralHello": "말하라.",
        "hateHello": "또 무슨 청인가.",
        "attacked": "천조에 맞서겠다는 것인가.",
        "defeated": "하늘의 뜻이 다하였구나.",
        "declaringWar": "천조의 군대가 너희를 벌하리라.",
        "tradeRequest": "조공을 바치러 왔는가."
    }
]
```

`Units.json` (전투 수치는 작업 8에서 조정한다. 대본용 유니크는 작업 6에서 추가한다):
```json
[
    {
        "name": "Panokseon",
        "unitType": "Ranged Water",
        "uniqueTo": "Joseon",
        "replaces": "Galleass",
        "movement": 4,
        "strength": 18,
        "rangedStrength": 20,
        "cost": 100,
        "requiredTech": "Compass",
        "uniques": ["Cannot enter ocean tiles"],
        "attackSound": "cannon"
    },
    {
        "name": "Turtle Ship",
        "unitType": "Melee Water",
        "uniqueTo": "Joseon",
        "replaces": "Caravel",
        "movement": 4,
        "strength": 28,
        "cost": 120,
        "requiredTech": "Astronomy",
        "upgradesTo": "Ironclad",
        "obsoleteTech": "Combustion",
        "hurryCostModifier": 30,
        "uniques": ["Cannot enter ocean tiles"],
        "attackSound": "cannon"
    },
    {
        "name": "Yi Sun-sin",
        "unitType": "Ranged Water",
        "uniqueTo": "Joseon",
        "movement": 4,
        "strength": 22,
        "rangedStrength": 22,
        "cost": 200,
        "uniques": ["Unbuildable", "Cannot enter ocean tiles", "[+15]% Strength bonus for [{Military} {Water}] units within [2] tiles"],
        "attackSound": "cannon"
    },
    {
        "name": "Atakebune",
        "unitType": "Ranged Water",
        "uniqueTo": "Toyotomi",
        "movement": 3,
        "strength": 16,
        "rangedStrength": 16,
        "cost": 100,
        "requiredTech": "Compass",
        "uniques": ["Cannot enter ocean tiles"],
        "attackSound": "arrow"
    },
    {
        "name": "Sekibune",
        "unitType": "Melee Water",
        "uniqueTo": "Toyotomi",
        "movement": 5,
        "strength": 14,
        "cost": 70,
        "requiredTech": "Sailing",
        "uniques": ["Cannot enter ocean tiles"]
    },
    {
        "name": "Japanese Transport",
        "unitType": "Melee Water",
        "uniqueTo": "Toyotomi",
        "movement": 4,
        "strength": 6,
        "cost": 40,
        "requiredTech": "Sailing",
        "uniques": ["Cannot attack", "Cannot enter ocean tiles"]
    }
]
```

`TileResources.json` (8개 모두 같은 형식):
```json
[
    {"name": "Naval Readiness", "resourceType": "Strategic", "uniques": ["Stockpiled", "Cannot be traded", "Not shown on world screen", "Will not be displayed in Civilopedia"]},
    {"name": "Popular Support", "resourceType": "Strategic", "uniques": ["Stockpiled", "Cannot be traded", "Not shown on world screen", "Will not be displayed in Civilopedia"]},
    {"name": "Court Unity", "resourceType": "Strategic", "uniques": ["Stockpiled", "Cannot be traded", "Not shown on world screen", "Will not be displayed in Civilopedia"]},
    {"name": "Ships Sunk", "resourceType": "Strategic", "uniques": ["Stockpiled", "Cannot be traded", "Not shown on world screen", "Will not be displayed in Civilopedia"]},
    {"name": "Defeat Flag", "resourceType": "Strategic", "uniques": ["Stockpiled", "Cannot be traded", "Not shown on world screen", "Will not be displayed in Civilopedia"]},
    {"name": "Okpo Speech Seen", "resourceType": "Strategic", "uniques": ["Stockpiled", "Cannot be traded", "Not shown on world screen", "Will not be displayed in Civilopedia"]},
    {"name": "Sacheon Event Seen", "resourceType": "Strategic", "uniques": ["Stockpiled", "Cannot be traded", "Not shown on world screen", "Will not be displayed in Civilopedia"]},
    {"name": "Waited For Yi Eok-gi", "resourceType": "Strategic", "uniques": ["Stockpiled", "Cannot be traded", "Not shown on world screen", "Will not be displayed in Civilopedia"]}
]
```

`Terrains.json`:
```json
[
    {"name": "Okpo Waters", "type": "TerrainFeature", "occursOn": ["Coast"], "uniques": ["Will not be displayed in Civilopedia"]},
    {"name": "Sacheon Waters", "type": "TerrainFeature", "occursOn": ["Coast"], "uniques": ["Will not be displayed in Civilopedia"]}
]
```

`Buildings.json` (대본 유니크는 작업 6에서 추가):
```json
[
    {"name": "Chapter 1 HQ", "cost": 0, "uniques": ["Unbuildable", "Will not be displayed in Civilopedia"]},
    {"name": "Japanese Command Ch1", "cost": 0, "uniques": ["Unbuildable", "Will not be displayed in Civilopedia"]}
]
```

`VictoryTypes.json`:
```json
[
    {
        "name": "Imjin Chapter 1",
        "victoryScreenHeader": "바다를 지켜냈다",
        "victoryString": "옥포에서 당항포까지, 조선 수군은 한 척도 잃지 않고 왜선 수십 척을 불살랐다. 바닷길이 막히자 북으로 올라간 왜군의 보급이 흔들리기 시작했다.\n\n2장 「학익진」에서 계속됩니다.",
        "defeatString": "",
        "milestones": ["Have at least [12] [Ships Sunk]", "Have at least [1] [[Yi Sun-sin] Units]"],
        "uniques": ["Only available <for [Joseon] Civilizations>", "Will not be chosen for new games"]
    },
    {
        "name": "Japanese Conquest",
        "hiddenInVictoryScreen": true,
        "victoryString": "",
        "defeatString": "남해의 바닷길이 왜군에게 열렸다. 왜선은 서해를 돌아 평양의 왜군에게 군량과 증원을 실어 날랐다.",
        "milestones": ["Have at least [1] [[Defeat Flag] resource of [Human player] Civilizations]"],
        "uniques": ["Only available <for [Toyotomi] Civilizations>", "Will not be chosen for new games"]
    }
]
```

`translations/Korean.properties` (UTF-8):
```properties
Joseon = 조선
Toyotomi = 도요토미 정권
Ming = 명
Seonjo = 선조
Toyotomi Hideyoshi = 도요토미 히데요시
Wanli Emperor = 만력제
Panokseon = 판옥선
Yi Sun-sin = 이순신
Atakebune = 아타케부네
Sekibune = 세키부네
Japanese Transport = 왜군 수송선
Naval Readiness = 수군
Popular Support = 민심
Court Unity = 조정
Ships Sunk = 격침한 적선
Defeat Flag = 패배
Okpo Speech Seen = 옥포 연설
Sacheon Event Seen = 사천 출전
Waited For Yi Eok-gi = 이억기 대기
Okpo Waters = 옥포 앞바다
Sacheon Waters = 사천 앞바다
Chapter 1 HQ = 1장 본영
Japanese Command Ch1 = 왜군 본영
Imjin Chapter 1 = 1장 「바다를 지켜라」
Japanese Conquest = 왜군의 승리
Imjin War = 임진왜란
Imjin War 1 - Guard the Sea = 임진왜란 1장 「바다를 지켜라」
Yeosu = 여수
Suncheon = 순천
Jinju = 진주
Hanseong = 한성
Pyeongyang = 평양
Uiju = 의주
Busan = 부산
Gimhae = 김해
Ungcheon = 웅천
Seosaengpo = 서생포
```

- [ ] **Step 6: 테스트 통과 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.campaign.ImjinModTest"`
Expected: 2개 PASS.

경고가 나오면 JSON을 고친다. 단언을 약하게 바꾸지 않는다. 경고별 처리:
- 자원 종류 관련: `"resourceType": "Strategic"`을 `"Bonus"`로 바꾼다. 비축은 종류와 무관하다.
- 마일스톤 텍스트: 메시지에 나온 유니크 문법으로 고친다.
- 해결할 수 없는 경고: 그 경고 문자열만 걸러내는 주석 달린 예외를 테스트에 넣고, 이유를 작업 보고에 쓴다.

- [ ] **Step 7: 게임에서 모드를 읽도록 정션 연결**

```powershell
New-Item -ItemType Directory -Force android\assets\mods | Out-Null
cmd /c mklink /J "android\assets\mods\Imjin War 1592" "campaign\Imjin War 1592"
```
Expected: `Junction created for ...`. `android/assets/mods/`는 `.gitignore` 대상이라 커밋되지 않는다.

- [ ] **Step 8: 커밋**

```powershell
git add tests/build.gradle.kts campaign/tools/src/com/unciv/campaign/CampaignEnvironment.kt campaign/tools/src/com/unciv/campaign/ImjinModTest.kt "campaign/Imjin War 1592/jsons" campaign/maps campaign/tools/mapgen
git commit -m "Imjin War mod: ruleset skeleton, chapter 1 map, and mod checker test" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### 작업 4: 시나리오 빌드 도구

**Files:**
- Create: `campaign/tools/src/com/unciv/campaign/AsciiMap.kt`
- Create: `campaign/tools/src/com/unciv/campaign/ScenarioBuilder.kt`
- Test: `campaign/tools/src/com/unciv/campaign/AsciiMapTest.kt`, `campaign/tools/src/com/unciv/campaign/ScenarioBuilderTest.kt`

**Interfaces:**
- Consumes: `CampaignEnvironment.init()`, `GameInfoPreview.getScenarioPlayers()`(작업 1), 작업 3의 룰셋 ID
- Produces:
  - `object AsciiMap { val legend: Map<Char, TerrainSpec>; fun parse(lines: List<String>, ruleset: Ruleset): TileMap; fun toHex(column: Int, line: Int, width: Int, height: Int): HexCoord }`
  - `class ScenarioBuilder(mapLines: List<String>, nations: List<String>, victoryTypes: List<String>, speed: String = "Imjin War", difficulty: String = "Prince")`
    - 속성: `gameInfo: GameInfo`, `ruleset: Ruleset`
    - 메서드: `civ(nation): Civilization`, `tile(column, line): Tile`, `addTechs(nation, techs: Collection<String>)`, `foundCity(nation, name, column, line, population = 1, buildings: List<String> = emptyList()): City`, `addUnit(nation, unit, column, line): MapUnit`, `declareWar(nation, target)`, `markWaters(feature, columns: IntRange, lines: IntRange)`, `finish(openingEvent: String? = null): GameInfo`
    - companion: `ScenarioBuilder.save(gameInfo: GameInfo, file: FileHandle)`
  - 좌표는 문자 지도에 쓰인 (열, 줄)이다. 줄 0이 북쪽이다.

- [ ] **Step 1: 실패하는 테스트 작성**

`campaign/tools/src/com/unciv/campaign/AsciiMapTest.kt`:
```kotlin
package com.unciv.campaign

import com.unciv.Constants
import com.unciv.models.metadata.BaseRuleset
import com.unciv.models.ruleset.RulesetCache
import com.unciv.testing.GdxTestRunner
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(GdxTestRunner::class)
class AsciiMapTest {
    @Before
    fun setUp() = CampaignEnvironment.init()

    private val ruleset get() = RulesetCache[BaseRuleset.Civ_V_GnK.fullName]!!

    @Test
    fun everyLegendCharBecomesItsTerrain() {
        val lines = listOf("~.gp", "fhm.")
        val map = AsciiMap.parse(lines, ruleset)
        fun at(column: Int, line: Int) = map[AsciiMap.toHex(column, line, 4, 2)]
        assertEquals(Constants.ocean, at(0, 0).baseTerrain)
        assertEquals(Constants.coast, at(1, 0).baseTerrain)
        assertEquals(Constants.grassland, at(2, 0).baseTerrain)
        assertEquals(Constants.plains, at(3, 0).baseTerrain)
        assertEquals(listOf(Constants.forest), at(0, 1).terrainFeatures)
        assertEquals(listOf(Constants.hill), at(1, 1).terrainFeatures)
        assertEquals(Constants.mountain, at(2, 1).baseTerrain)
        assertEquals(8, map.values.size)
    }

    @Test
    fun firstLineIsNorth() {
        val map = AsciiMap.parse(listOf("g", "."), ruleset)
        val north = map[AsciiMap.toHex(0, 0, 1, 2)]
        val south = map[AsciiMap.toHex(0, 1, 1, 2)]
        assertEquals(1, north.getRow() - south.getRow())
    }

    @Test(expected = IllegalArgumentException::class)
    fun unknownCharsAreRejected() {
        AsciiMap.parse(listOf("gx"), ruleset)
    }

    @Test(expected = IllegalArgumentException::class)
    fun raggedLinesAreRejected() {
        AsciiMap.parse(listOf("gg", "g"), ruleset)
    }
}
```

`campaign/tools/src/com/unciv/campaign/ScenarioBuilderTest.kt`:
```kotlin
package com.unciv.campaign

import com.unciv.json.json
import com.unciv.logic.GameInfoPreview
import com.unciv.logic.civilization.AlertType
import com.unciv.logic.civilization.PlayerType
import com.unciv.logic.files.UncivFiles
import com.unciv.testing.GdxTestRunner
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(GdxTestRunner::class)
class ScenarioBuilderTest {
    private val map = listOf(
        "gggg..",
        "gggg..",
        "gg....",
        "gg....",
    )
    private lateinit var builder: ScenarioBuilder

    @Before
    fun setUp() {
        CampaignEnvironment.init()
        builder = ScenarioBuilder(map, listOf("Joseon", "Toyotomi"), listOf("Imjin Chapter 1"))
    }

    @Test
    fun firstNationIsTheHumanAndHasTheTurn() {
        assertEquals(PlayerType.Human, builder.civ("Joseon").playerType)
        assertEquals(PlayerType.AI, builder.civ("Toyotomi").playerType)
        assertEquals("Joseon", builder.gameInfo.currentPlayer)
        assertEquals(1592, builder.gameInfo.getYear())
    }

    @Test
    fun foundsNamedCitiesWithBuildings() {
        val city = builder.foundCity("Joseon", "Yeosu", 1, 1, population = 3, buildings = listOf("Chapter 1 HQ"))
        assertEquals("Yeosu", city.name)
        assertEquals(3, city.population.population)
        assertTrue(city.cityConstructions.isBuilt("Chapter 1 HQ"))
        assertEquals(city, builder.civ("Joseon").getCapital())
    }

    @Test
    fun placesShipsAndDeclaresWar() {
        builder.foundCity("Toyotomi", "Busan", 2, 0)
        val ship = builder.addUnit("Toyotomi", "Atakebune", 5, 1)
        assertTrue(ship.getTile().isWater)
        builder.declareWar("Toyotomi", "Joseon")
        assertTrue(builder.civ("Joseon").isAtWarWith(builder.civ("Toyotomi")))
    }

    @Test
    fun marksOnlyCoastTiles() {
        builder.markWaters("Okpo Waters", 3..5, 0..1)
        val marked = builder.gameInfo.tileMap.values.filter { "Okpo Waters" in it.terrainFeatures }
        assertEquals(4, marked.size)
        assertTrue(marked.all { it.isWater })
    }

    @Test
    fun finishQueuesOnlyTheOpeningEvent() {
        builder.addTechs("Joseon", listOf("Compass"))
        builder.declareWar("Toyotomi", "Joseon")
        val game = builder.finish("Prologue Envoys")
        val alerts = game.getCivilization("Joseon").popupAlerts
        assertEquals(listOf(AlertType.Event to "Prologue Envoys"), alerts.map { it.type to it.value })
        assertFalse(game.getCivilization("Toyotomi").popupAlerts.any())
    }

    @Test
    fun savedScenarioRoundTrips() {
        builder.foundCity("Joseon", "Yeosu", 1, 1)
        val text = UncivFiles.gameInfoToString(builder.finish(), forceZip = false)
        UncivFiles.gameInfoFromString(text) // throws if the save cannot be loaded
        val players = json().fromJson(GameInfoPreview::class.java, text).getScenarioPlayers()
        assertEquals("Joseon", players.single { it.playerType == PlayerType.Human }.chosenCiv)
    }
}
```

- [ ] **Step 2: 실패 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.campaign.*"`
Expected: 컴파일 실패, `Unresolved reference 'AsciiMap'`, `'ScenarioBuilder'`.

- [ ] **Step 3: AsciiMap 구현**

`campaign/tools/src/com/unciv/campaign/AsciiMap.kt`:
```kotlin
package com.unciv.campaign

import com.unciv.Constants
import com.unciv.logic.map.HexCoord
import com.unciv.logic.map.HexMath
import com.unciv.logic.map.MapShape
import com.unciv.logic.map.MapSize
import com.unciv.logic.map.TileMap
import com.unciv.models.ruleset.Ruleset

/** Turns a text map - one char per tile, first line = north - into a rectangular [TileMap].
 *  Unciv's rectangular maps are columns of flat-topped hexes; odd columns sit half a tile further north. */
object AsciiMap {
    class TerrainSpec(val baseTerrain: String, val features: List<String> = emptyList())

    val legend = mapOf(
        '~' to TerrainSpec(Constants.ocean),
        '.' to TerrainSpec(Constants.coast),
        'g' to TerrainSpec(Constants.grassland),
        'p' to TerrainSpec(Constants.plains),
        'f' to TerrainSpec(Constants.grassland, listOf(Constants.forest)),
        'h' to TerrainSpec(Constants.grassland, listOf(Constants.hill)),
        'm' to TerrainSpec(Constants.mountain),
    )

    fun parse(lines: List<String>, ruleset: Ruleset): TileMap {
        val rows = lines.filter { it.isNotBlank() }
        val height = rows.size
        val width = rows.first().length
        require(rows.all { it.length == width }) { "All map lines must be $width chars long" }

        val tileMap = TileMap(width, height, ruleset, false)
        tileMap.mapParameters.shape = MapShape.rectangular
        tileMap.mapParameters.mapSize = MapSize(width, height)
        for ((line, text) in rows.withIndex())
            for ((column, char) in text.withIndex()) {
                val spec = legend[char]
                    ?: throw IllegalArgumentException("Unknown map char '$char' at column $column, line $line")
                val tile = tileMap[toHex(column, line, width, height)]
                tile.baseTerrain = spec.baseTerrain
                tile.setTerrainFeatures(spec.features)
                tile.setTerrainTransients()
            }
        return tileMap
    }

    /** ([column], [line]) as written in the text map → hex coordinate in a [width] x [height] rectangular map */
    fun toHex(column: Int, line: Int, width: Int, height: Int): HexCoord =
        HexMath.getTileCoordsFromColumnRow(column - width / 2, (height - 1) / 2 - line)
}
```

- [ ] **Step 4: ScenarioBuilder 구현**

`campaign/tools/src/com/unciv/campaign/ScenarioBuilder.kt`:
```kotlin
package com.unciv.campaign

import com.badlogic.gdx.files.FileHandle
import com.unciv.Constants
import com.unciv.logic.GameInfo
import com.unciv.logic.city.City
import com.unciv.logic.civilization.AlertType
import com.unciv.logic.civilization.Civilization
import com.unciv.logic.civilization.PlayerType
import com.unciv.logic.civilization.PopupAlert
import com.unciv.logic.files.UncivFiles
import com.unciv.logic.map.TileMap
import com.unciv.logic.map.mapunit.MapUnit
import com.unciv.logic.map.tile.Tile
import com.unciv.models.metadata.BaseRuleset
import com.unciv.models.metadata.Player
import com.unciv.models.ruleset.Ruleset
import com.unciv.models.ruleset.RulesetCache

/**
 * Builds a scenario save the way GameStarter builds a new game, but from a fixed text map and a fixed cast.
 * The first of [nations] is the human player. Positions are (column, line) as written in the text map, line 0 = north.
 */
class ScenarioBuilder(
    mapLines: List<String>,
    private val nations: List<String>,
    victoryTypes: List<String>,
    speed: String = "Imjin War",
    difficulty: String = "Prince",
) {
    val gameInfo = GameInfo()
    val ruleset: Ruleset
    private val width = mapLines.first { it.isNotBlank() }.length
    private val height = mapLines.count { it.isNotBlank() }

    init {
        gameInfo.gameParameters.apply {
            baseRuleset = BaseRuleset.Civ_V_GnK.fullName
            mods = linkedSetOf(CampaignEnvironment.MOD_NAME)
            this.speed = speed
            this.difficulty = difficulty
            noBarbarians = true
            numberOfCityStates = 0
            this.victoryTypes = ArrayList(victoryTypes)
            players = nations.mapIndexedTo(ArrayList()) { index, nation ->
                Player(nation, if (index == 0) PlayerType.Human else PlayerType.AI)
            }
        }
        gameInfo.difficulty = difficulty
        ruleset = RulesetCache.getComplexRuleset(gameInfo.gameParameters)
        gameInfo.ruleset = ruleset

        val tileMap = AsciiMap.parse(mapLines, ruleset)
        gameInfo.tileMap = tileMap
        tileMap.gameInfo = gameInfo

        for ((index, nationName) in nations.withIndex()) {
            val nation = ruleset.nations[nationName] ?: error("Nation $nationName is not in the ruleset")
            val civ = Civilization(nation)
            civ.playerType = if (index == 0) PlayerType.Human else PlayerType.AI
            gameInfo.civilizations.add(civ)
        }
        gameInfo.currentPlayer = nations.first()
        gameInfo.historyStartTurn = 0
        tileMap.assignContinents(TileMap.AssignContinentsMode.Ensure)
        tileMap.setTransients(ruleset)
        gameInfo.setTransients()
    }

    fun civ(nation: String): Civilization = gameInfo.getCivilization(nation)

    fun tile(column: Int, line: Int): Tile = gameInfo.tileMap[AsciiMap.toHex(column, line, width, height)]

    /** Researches [techs] and everything they require, without notifications */
    fun addTechs(nation: String, techs: Collection<String>) {
        val civ = civ(nation)
        fun research(name: String) {
            if (civ.tech.isResearched(name)) return
            val tech = ruleset.technologies[name] ?: error("Unknown tech $name")
            for (prerequisite in tech.prerequisites) research(prerequisite)
            civ.tech.addTechnology(name, false)
        }
        techs.forEach(::research)
    }

    /** The first city founded by a nation becomes its capital */
    fun foundCity(nation: String, name: String, column: Int, line: Int, population: Int = 1, buildings: List<String> = emptyList()): City {
        val city = civ(nation).addCity(tile(column, line).position)
        city.name = name
        if (population > 1) city.population.addPopulation(population - 1)
        for (building in buildings) city.cityConstructions.addBuilding(building)
        return city
    }

    /** Places [unit] on the given tile, or the nearest tile it can stand on */
    fun addUnit(nation: String, unit: String, column: Int, line: Int): MapUnit =
        civ(nation).units.placeUnitNearTile(tile(column, line).position, unit)
            ?: error("Could not place $unit near ($column, $line)")

    fun declareWar(nation: String, target: String) {
        val civ = civ(nation)
        civ.diplomacyFunctions.makeCivilizationsMeet(civ(target))
        civ.getDiplomacyManager(target)!!.declareWar()
    }

    /** Lays the invisible terrain feature [feature] on every Coast tile in the rectangle, so unit triggers can match "[feature]" tiles */
    fun markWaters(feature: String, columns: IntRange, lines: IntRange) {
        require(feature in ruleset.terrains) { "Terrain feature $feature is not in the ruleset" }
        for (line in lines)
            for (column in columns) {
                val tile = tile(column, line)
                if (tile.baseTerrain == Constants.coast) tile.addTerrainFeature(feature)
            }
    }

    /** Drops the popups the setup produced (techs, contact, war), queues [openingEvent] for the human
     *  so it shows as soon as the scenario starts, and gives every unit its full movement */
    fun finish(openingEvent: String? = null): GameInfo {
        for (civ in gameInfo.civilizations) civ.popupAlerts.clear()
        if (openingEvent != null) civ(nations.first()).popupAlerts.add(PopupAlert(AlertType.Event, openingEvent))
        for (civ in gameInfo.civilizations)
            for (unit in civ.units.getCivUnits()) unit.currentMovement = unit.getMaxMovement().toFloat()
        return gameInfo
    }

    companion object {
        fun save(gameInfo: GameInfo, file: FileHandle) {
            file.parent().mkdirs()
            file.writeString(UncivFiles.gameInfoToString(gameInfo, forceZip = false), false, Charsets.UTF_8.name())
        }
    }
}
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.campaign.*"`
Expected: `AsciiMapTest` 4개, `ScenarioBuilderTest` 6개, `ImjinModTest` 2개 PASS.

`firstNationIsTheHumanAndHasTheTurn`의 연도가 1592가 아니면 `GameInfo.getYear()`(346행)와 `Speed.turnToYear`를 확인해 `Speeds.json`의 `startYear`를 고친다.

- [ ] **Step 6: 커밋**

```powershell
git add campaign/tools/src/com/unciv/campaign/AsciiMap.kt campaign/tools/src/com/unciv/campaign/ScenarioBuilder.kt campaign/tools/src/com/unciv/campaign/AsciiMapTest.kt campaign/tools/src/com/unciv/campaign/ScenarioBuilderTest.kt
git commit -m "Campaign tools: build scenario saves from a text map and a fixed cast" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### 작업 5: 1장 배치와 시나리오 생성

**Files:**
- Create: `campaign/tools/src/com/unciv/campaign/Chapter1.kt`
- Create: `campaign/tools/src/com/unciv/campaign/BuildScenarios.kt`
- Modify: `tests/build.gradle.kts` (`buildScenarios` 태스크 추가)
- Test: `campaign/tools/src/com/unciv/campaign/Chapter1ScenarioTest.kt`
- Generated: `campaign/Imjin War 1592/scenarios/Imjin War 1 - Guard the Sea`

**Interfaces:**
- Consumes: `ScenarioBuilder`(작업 4), `campaign/maps/ch1-south-sea.txt`
- Produces: `object Chapter1 { const val FILE_NAME, VICTORY, JAPANESE_VICTORY, OPENING_EVENT, HQ, JAPANESE_HQ; fun build(): GameInfo }`. 작업 6, 8이 쓴다.

배치 좌표는 `campaign/maps/ch1-south-sea.txt` 기준으로 모두 검증했다(도시는 육지, 함선은 `.` 연안).

| 대상 | 좌표 (열, 줄) |
|---|---|
| 조선 도시 | 여수 (9,18) 수도, 순천 (2,11), 진주 (19,4) |
| 일본 도시 | 부산 (46,6) 수도, 김해 (40,2) |
| 조선 함대 | 이순신 (10,18), 판옥선 (11,18) (10,17) (10,19) |
| 일본 함대: 옥포 | (38,13) (38,14) (39,13) (38,15) |
| 일본 함대: 합포 | (32,6) (33,6) |
| 일본 함대: 적진포 | (29,9) (30,9) |
| 일본 함대: 사천 | (18,10) (19,11) (18,12) |
| 일본 함대: 당포 | (25,17) (26,17) (24,16) |
| 일본 함대: 당항포 | (32,7) (33,7) (31,8) |
| 해역 | 옥포 열 37..40 × 줄 11..16 (연안 18칸), 사천 열 16..20 × 줄 8..13 (연안 14칸) |

- [ ] **Step 1: 실패하는 테스트 작성**

`campaign/tools/src/com/unciv/campaign/Chapter1ScenarioTest.kt`:
```kotlin
package com.unciv.campaign

import com.unciv.logic.GameInfo
import com.unciv.testing.GdxTestRunner
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(GdxTestRunner::class)
class Chapter1ScenarioTest {
    private lateinit var game: GameInfo
    private val joseon get() = game.getCivilization("Joseon")
    private val japan get() = game.getCivilization("Toyotomi")

    @Before
    fun setUp() {
        CampaignEnvironment.init()
        game = Chapter1.build()
    }

    @Test
    fun castCitiesAndFleetsArePlaced() {
        assertTrue(joseon.isHuman())
        assertFalse(japan.isHuman())
        assertTrue(joseon.isAtWarWith(japan))
        assertEquals("Yeosu", joseon.getCapital()!!.name)
        assertTrue(joseon.getCapital()!!.cityConstructions.isBuilt(Chapter1.HQ))
        assertEquals("Busan", japan.getCapital()!!.name)
        assertTrue(japan.getCapital()!!.cityConstructions.isBuilt(Chapter1.JAPANESE_HQ))
        assertEquals(1, joseon.units.getCivUnits().count { it.name == "Yi Sun-sin" })
        assertEquals(3, joseon.units.getCivUnits().count { it.name == "Panokseon" })
        assertEquals(17, japan.units.getCivUnits().count { it.baseUnit.unitType.endsWith("Water") })
        assertEquals(18, game.tileMap.values.count { "Okpo Waters" in it.terrainFeatures })
        assertEquals(14, game.tileMap.values.count { "Sacheon Waters" in it.terrainFeatures })
    }

    @Test
    fun opensWithThePrologue() {
        assertEquals(listOf(Chapter1.OPENING_EVENT), joseon.popupAlerts.map { it.value })
    }

    @Test
    fun sinkingTwelveShipsWinsTheChapter() {
        joseon.resourceStockpiles.add("Ships Sunk", 11)
        assertNull(joseon.victoryManager.getVictoryTypeAchieved())
        joseon.resourceStockpiles.add("Ships Sunk", 1)
        assertEquals(Chapter1.VICTORY, joseon.victoryManager.getVictoryTypeAchieved())
    }

    @Test
    fun defeatFlagMakesJapanWin() {
        assertNull(japan.victoryManager.getVictoryTypeAchieved())
        joseon.resourceStockpiles.add("Defeat Flag", 1)
        assertEquals(Chapter1.JAPANESE_VICTORY, japan.victoryManager.getVictoryTypeAchieved())
    }
}
```

- [ ] **Step 2: 실패 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.campaign.Chapter1ScenarioTest"`
Expected: 컴파일 실패, `Unresolved reference 'Chapter1'`.

- [ ] **Step 3: Chapter1 구현**

`campaign/tools/src/com/unciv/campaign/Chapter1.kt`:
```kotlin
package com.unciv.campaign

import com.badlogic.gdx.files.FileHandle
import com.unciv.logic.GameInfo

/** Chapter 1 "Guard the Sea": the 1st and 2nd sorties, Okpo to Danghangpo, May-June 1592.
 *  Positions are (column, line) in campaign/maps/ch1-south-sea.txt. */
object Chapter1 {
    const val FILE_NAME = "Imjin War 1 - Guard the Sea"
    const val VICTORY = "Imjin Chapter 1"
    const val JAPANESE_VICTORY = "Japanese Conquest"
    const val OPENING_EVENT = "Prologue Envoys"
    const val HQ = "Chapter 1 HQ"
    const val JAPANESE_HQ = "Japanese Command Ch1"
    private const val JOSEON = "Joseon"
    private const val JAPAN = "Toyotomi"
    private val techs = listOf("Compass", "Astronomy", "Steel", "Civil Service", "Machinery")

    fun mapLines(): List<String> =
        FileHandle("${CampaignEnvironment.CAMPAIGN_FOLDER}/maps/ch1-south-sea.txt")
            .readString(Charsets.UTF_8.name()).lines().filter { it.isNotBlank() }

    fun build(): GameInfo {
        val builder = ScenarioBuilder(mapLines(), listOf(JOSEON, JAPAN), listOf(VICTORY, JAPANESE_VICTORY))
        with(builder) {
            addTechs(JOSEON, techs)
            addTechs(JAPAN, techs)

            foundCity(JOSEON, "Yeosu", 9, 18, population = 3, buildings = listOf(HQ, "Walls"))
            foundCity(JOSEON, "Suncheon", 2, 11, population = 2, buildings = listOf("Walls"))
            foundCity(JOSEON, "Jinju", 19, 4, population = 3, buildings = listOf("Walls"))
            foundCity(JAPAN, "Busan", 46, 6, population = 3, buildings = listOf(JAPANESE_HQ, "Walls"))
            foundCity(JAPAN, "Gimhae", 40, 2, population = 2)
            declareWar(JAPAN, JOSEON)

            markWaters("Okpo Waters", 37..40, 11..16)
            markWaters("Sacheon Waters", 16..20, 8..13)

            // Jeolla Left Navy, at Yeosu
            addUnit(JOSEON, "Yi Sun-sin", 10, 18)
            for ((column, line) in listOf(11 to 18, 10 to 17, 10 to 19)) addUnit(JOSEON, "Panokseon", column, line)
            for ((column, line) in listOf(9 to 18, 2 to 11, 19 to 4)) addUnit(JOSEON, "Pikeman", column, line)

            // Japanese fleets anchored along the coast
            japaneseFleet("Atakebune" at (38 to 13), "Atakebune" at (38 to 14), "Sekibune" at (39 to 13), "Japanese Transport" at (38 to 15)) // Okpo
            japaneseFleet("Sekibune" at (32 to 6), "Japanese Transport" at (33 to 6)) // Happo
            japaneseFleet("Atakebune" at (29 to 9), "Japanese Transport" at (30 to 9)) // Jeokjinpo
            japaneseFleet("Atakebune" at (18 to 10), "Sekibune" at (19 to 11), "Sekibune" at (18 to 12)) // Sacheon
            japaneseFleet("Atakebune" at (25 to 17), "Sekibune" at (26 to 17), "Sekibune" at (24 to 16)) // Dangpo
            japaneseFleet("Atakebune" at (32 to 7), "Atakebune" at (33 to 7), "Japanese Transport" at (31 to 8)) // Danghangpo
            for ((column, line) in listOf(46 to 6, 40 to 2)) addUnit(JAPAN, "Longswordsman", column, line)
        }
        return builder.finish(OPENING_EVENT)
    }

    private infix fun String.at(position: Pair<Int, Int>) = this to position

    private fun ScenarioBuilder.japaneseFleet(vararg ships: Pair<String, Pair<Int, Int>>) {
        for ((unit, position) in ships) addUnit(JAPAN, unit, position.first, position.second)
    }
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.campaign.Chapter1ScenarioTest"`
Expected: 4개 PASS.

`defeatFlagMakesJapanWin`이 실패하면 이정표의 중첩 대괄호 해석 문제다. 이 경우 `VictoryTypes.json`의 `Japanese Conquest`를 다음처럼 바꾼다.
- 이정표: `"Have at least [1] [Defeat Flag]"`
- 플래그 기록: 작업 6에서 패배 플래그를 조선 대신 일본 수도의 `Japanese Command Ch1`이 기록하게 한다. 조건은 `<when number of [[Defeat Flag] resource of [Human player] Civilizations] is more than [0]>`이다.

같은 실패가 `Yi Sun-sin` 이정표에서 나면, 그 이정표를 지우고 작업 6의 패배 처리에만 맡긴다. 어떤 방식을 택했는지 작업 보고에 쓴다.

- [ ] **Step 5: 생성 진입점과 Gradle 태스크**

`campaign/tools/src/com/unciv/campaign/BuildScenarios.kt`:
```kotlin
package com.unciv.campaign

import com.badlogic.gdx.files.FileHandle

/** Regenerates the campaign scenario saves. Run from the repo root: gradlew :tests:buildScenarios */
fun main() {
    CampaignEnvironment.init()
    val scenarios = FileHandle("${CampaignEnvironment.MOD_FOLDER}/scenarios")
    val chapter1 = scenarios.child(Chapter1.FILE_NAME)
    ScenarioBuilder.save(Chapter1.build(), chapter1)
    println("Wrote ${chapter1.file().canonicalPath}")
}
```

`tests/build.gradle.kts` 끝에 추가:
```kotlin
// Imjin War campaign: regenerates the scenario saves in campaign/Imjin War 1592/scenarios
tasks.register<JavaExec>("buildScenarios") {
    group = "campaign"
    description = "Builds the Imjin War campaign scenario saves"
    classpath = sourceSets.test.get().runtimeClasspath
    mainClass.set("com.unciv.campaign.BuildScenariosKt")
    workingDir = file("../android/assets")
}
```

- [ ] **Step 6: 시나리오 생성**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:buildScenarios`
Expected: `Wrote C:\c_e\testgame\Unciv\campaign\Imjin War 1592\scenarios\Imjin War 1 - Guard the Sea`, `BUILD SUCCESSFUL`. 파일이 JSON 텍스트로 시작하는지(`{`) 확인한다.

- [ ] **Step 7: 커밋**

```powershell
git add campaign/tools/src/com/unciv/campaign/Chapter1.kt campaign/tools/src/com/unciv/campaign/BuildScenarios.kt campaign/tools/src/com/unciv/campaign/Chapter1ScenarioTest.kt tests/build.gradle.kts "campaign/Imjin War 1592/scenarios" "campaign/Imjin War 1592/jsons"
git commit -m "Imjin War chapter 1: map placement, victory conditions, and generated scenario" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### 작업 6: 1장 대본 (이벤트, 본영 건물, 유닛 발동)

**Files:**
- Create: `campaign/Imjin War 1592/jsons/Events.json`
- Modify: `campaign/Imjin War 1592/jsons/Buildings.json`, `campaign/Imjin War 1592/jsons/Units.json`
- Test: `campaign/tools/src/com/unciv/campaign/Chapter1ScriptTest.kt`
- Regenerate: `campaign/Imjin War 1592/scenarios/Imjin War 1 - Guard the Sea`

**Interfaces:**
- Consumes:
  - `Event.speaker`, `Event.portrait`(작업 2)
  - `Chapter1.build()`(작업 5)
  - 초상화 이름 `Portraits/<인물>`, 장면 이름 `Scenes/<장면>`(작업 7에서 실제 파일이 생긴다. 그 전에는 이미지 없이 이름만 표시된다)
- Produces: 이벤트 이름 `Prologue Envoys`, `Prologue Hwang`, `Prologue Kim`, `Prologue Seonjo`, `Prologue Ryu`, `Briefing Busan`, `Briefing Won Gyun`, `Briefing Decision`, `Okpo Speech`, `Sacheon Sortie`, `Yi Fallen`, `Chapter 1 Timeout`

**흐름:**
- 시작: `Prologue Envoys` → `Prologue Hwang` → `Prologue Kim` → `Prologue Seonjo`(선택) → `Prologue Ryu`(선택) → `Briefing Busan` → `Briefing Won Gyun` → `Briefing Decision`(선택). 각 이벤트의 선택지가 다음 이벤트를 띄운다.
- 전투 중: 이순신이 옥포 해역에 처음 들어가면 `Okpo Speech`, 사천 해역에 처음 들어가면 `Sacheon Sortie`(거북선 1척 추가)
- 패배: `Chapter 1 HQ`가 매 턴 시작에 검사한다. 이순신이 없거나, 턴 40(이억기를 기다렸으면 36)에 이르면 `Defeat Flag`를 올리고 사유 이벤트를 한 번 띄운다. 그러면 `Japanese Conquest`가 성립한다.
- 승리: 조선 함선이 물 위 유닛을 격침할 때마다 `Ships Sunk` +1. 12척이면 `Imjin Chapter 1`.
- 일본 증원: `Japanese Command Ch1`이 6턴마다 부산에 세키부네 2척을 만든다.

- [ ] **Step 1: 실패하는 테스트 작성**

`campaign/tools/src/com/unciv/campaign/Chapter1ScriptTest.kt`:
```kotlin
package com.unciv.campaign

import com.unciv.Constants
import com.unciv.logic.GameInfo
import com.unciv.logic.battle.Battle
import com.unciv.logic.battle.MapUnitCombatant
import com.unciv.logic.city.managers.CityTurnManager
import com.unciv.logic.civilization.AlertType
import com.unciv.models.ruleset.unique.UniqueType
import com.unciv.testing.GdxTestRunner
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(GdxTestRunner::class)
class Chapter1ScriptTest {
    private lateinit var game: GameInfo
    private val joseon get() = game.getCivilization("Joseon")
    private val japan get() = game.getCivilization("Toyotomi")
    private val yi get() = joseon.units.getCivUnits().first { it.name == "Yi Sun-sin" }

    @Before
    fun setUp() {
        CampaignEnvironment.init()
        game = Chapter1.build()
    }

    private fun eventAlerts(event: String) = joseon.popupAlerts.count {
        it.type == AlertType.Event && it.value.substringBefore(Constants.stringSplitCharacter) == event
    }

    private fun choose(event: String, choice: Int) = game.ruleset.events[event]!!.choices[choice].triggerChoice(joseon)

    private fun startTurnIn(city: String) = CityTurnManager(game.getCities().first { it.name == city }).startTurn()

    @Test
    fun prologueChainsIntoTheSortieDecision() {
        val chain = mutableListOf(Chapter1.OPENING_EVENT)
        while (true) {
            val next = game.ruleset.events[chain.last()]!!.choices.first().uniqueObjects
                .firstOrNull { it.type == UniqueType.TriggerEvent }?.params?.get(0) ?: break
            chain += next
        }
        assertEquals(listOf("Prologue Envoys", "Prologue Hwang", "Prologue Kim", "Prologue Seonjo", "Prologue Ryu",
            "Briefing Busan", "Briefing Won Gyun", "Briefing Decision"), chain)
    }

    @Test
    fun preparingTheSeaGivesAShipAndNavalReadiness() {
        choose("Prologue Seonjo", 0)
        assertEquals(1, joseon.getResourceAmount("Naval Readiness"))
        assertEquals(4, joseon.units.getCivUnits().count { it.name == "Panokseon" })
        assertEquals(1, eventAlerts("Prologue Ryu"))
    }

    @Test
    fun supportingTheTurtleShipLaunchesOne() {
        choose("Prologue Ryu", 0)
        assertEquals(1, joseon.units.getCivUnits().count { it.name == "Turtle Ship" })
        assertEquals(1, eventAlerts("Briefing Busan"))
    }

    @Test
    fun okpoSpeechPlaysOnlyOnce() {
        val okpo = game.tileMap.values.filter { "Okpo Waters" in it.terrainFeatures && it.militaryUnit == null }
        yi.moveThroughTile(okpo[0])
        yi.moveThroughTile(okpo[1])
        assertEquals(1, eventAlerts("Okpo Speech"))
        assertEquals(1, joseon.getResourceAmount("Okpo Speech Seen"))
    }

    @Test
    fun sacheonSortieLaunchesTheTurtleShip() {
        val sacheon = game.tileMap.values.first { "Sacheon Waters" in it.terrainFeatures && it.militaryUnit == null }
        yi.moveThroughTile(sacheon)
        assertEquals(1, eventAlerts("Sacheon Sortie"))
        choose("Sacheon Sortie", 0)
        assertEquals(1, joseon.units.getCivUnits().count { it.name == "Turtle Ship" })
    }

    @Test
    fun losingYiSunSinLosesTheChapter() {
        yi.destroy()
        startTurnIn("Yeosu")
        startTurnIn("Yeosu")
        assertEquals(1, eventAlerts("Yi Fallen"))
        assertTrue(joseon.getResourceAmount("Defeat Flag") >= 1)
        assertEquals(Chapter1.JAPANESE_VICTORY, japan.victoryManager.getVictoryTypeAchieved())
    }

    @Test
    fun runningOutOfTimeLosesTheChapter() {
        game.turns = 39
        startTurnIn("Yeosu")
        assertEquals(0, joseon.getResourceAmount("Defeat Flag"))
        game.turns = 40
        startTurnIn("Yeosu")
        startTurnIn("Yeosu")
        assertEquals(1, eventAlerts("Chapter 1 Timeout"))
        assertTrue(joseon.getResourceAmount("Defeat Flag") >= 1)
    }

    @Test
    fun waitingForYiEokGiShortensTheTimeLimit() {
        choose("Briefing Decision", 1)
        assertEquals(5, joseon.units.getCivUnits().count { it.name == "Panokseon" })
        game.turns = 36
        startTurnIn("Yeosu")
        assertEquals(1, eventAlerts("Chapter 1 Timeout"))
    }

    @Test
    fun sinkingAShipCountsTowardsVictory() {
        val transport = japan.units.getCivUnits().first { it.name == "Japanese Transport" }
        val turtle = joseon.units.placeUnitNearTile(transport.getTile().position, "Turtle Ship")!!
        transport.health = 1
        Battle.attack(MapUnitCombatant(turtle), MapUnitCombatant(transport))
        assertTrue(transport.isDestroyed)
        assertEquals(1, joseon.getResourceAmount("Ships Sunk"))
    }

    @Test
    fun japanReinforcesBusanEverySixTurns() {
        val before = japan.units.getCivUnits().count { it.name == "Sekibune" }
        game.turns = 6
        startTurnIn("Busan")
        assertEquals(before + 2, japan.units.getCivUnits().count { it.name == "Sekibune" })
    }
}
```

- [ ] **Step 2: 실패 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.campaign.Chapter1ScriptTest"`
Expected: 여러 테스트 FAIL. 예: `NullPointerException`(이벤트 없음), `expected:<1> but was:<0>`.

- [ ] **Step 3: Events.json 작성**

`campaign/Imjin War 1592/jsons/Events.json`:
```json
[
    {
        "name": "Prologue Envoys",
        "civilopediaText": [
            {"header": 3, "text": "1591년 3월, 한성"},
            {"text": "일본에 갔던 통신사가 돌아왔다. 정사 황윤길과 부사 김성일은 같은 것을 보고 왔으나, 임금 앞에서 서로 다른 말을 했다."}
        ],
        "choices": [ {"text": "보고를 듣는다", "uniques": ["Triggers a [Prologue Hwang] event"]} ]
    },
    {
        "name": "Prologue Hwang",
        "speaker": "황윤길",
        "portrait": "Portraits/Hwang Yun-gil",
        "text": "반드시 병화가 있을 것입니다. 히데요시는 눈빛이 반짝이고 담과 지략이 있어 보였습니다. 이미 배를 모으고 군사를 조련하고 있습니다.",
        "choices": [ {"text": "계속", "uniques": ["Triggers a [Prologue Kim] event"]} ]
    },
    {
        "name": "Prologue Kim",
        "speaker": "김성일",
        "portrait": "Portraits/Kim Seong-il",
        "text": "그러한 정황은 보지 못하였습니다. 히데요시는 눈이 쥐와 같아 두려워할 위인이 못 됩니다. 공연히 인심을 흔들어서는 아니 됩니다.",
        "choices": [ {"text": "계속", "uniques": ["Triggers a [Prologue Seonjo] event"]} ]
    },
    {
        "name": "Prologue Seonjo",
        "speaker": "선조",
        "portrait": "Portraits/Seonjo",
        "text": "두 사람의 말이 이토록 다르니, 과인은 어느 말을 믿어야 하는가.",
        "choices": [
            {"text": "황윤길의 말을 따라 남쪽 바다를 대비한다", "uniques": ["Instantly provides [1] [Naval Readiness]", "Free [Panokseon] appears", "Triggers a [Prologue Ryu] event"]},
            {"text": "김성일의 말을 따라 백성을 안심시킨다", "uniques": ["Instantly provides [1] [Popular Support]", "Gain [150] [Gold]", "Triggers a [Prologue Ryu] event"]}
        ]
    },
    {
        "name": "Prologue Ryu",
        "speaker": "류성룡",
        "portrait": "Portraits/Ryu Seong-ryong",
        "text": "전라좌수사로 천거한 이순신이 좌수영에서 새 배를 짓고 있다 하옵니다. 판옥선 위에 거북의 등처럼 덮개를 씌우고 쇠못을 꽂은 배라 하옵니다. 조정에서 힘을 실어 주시옵소서.",
        "choices": [
            {"text": "거북선 건조를 지원하라", "uniques": ["Free [Turtle Ship] appears", "Instantly provides [1] [Naval Readiness]", "Triggers a [Briefing Busan] event"]},
            {"text": "국고를 아끼고 조정의 기강을 세운다", "uniques": ["Instantly provides [1] [Court Unity]", "Gain [100] [Gold]", "Triggers a [Briefing Busan] event"]}
        ]
    },
    {
        "name": "Briefing Busan",
        "civilopediaText": [
            {"extraImage": "Scenes/Busan Falls", "imageSize": 480, "centered": true},
            {"header": 3, "text": "1592년 4월 13일, 부산포"},
            {"text": "왜군 선봉 고니시 유키나가의 1만 8천 명이 부산포에 올랐다. 부산진 첨사 정발과 동래부사 송상현이 끝까지 싸우다 전사했다."},
            {"text": "경상좌수사 박홍은 진을 버리고 달아났고, 경상우수사 원균은 스스로 배를 가라앉힌 채 겨우 몇 척만 이끌고 물러났다. 왜군은 보름 만에 한성 가까이 이르렀다."}
        ],
        "choices": [ {"text": "계속", "uniques": ["Triggers a [Briefing Won Gyun] event"]} ]
    },
    {
        "name": "Briefing Won Gyun",
        "speaker": "원균",
        "portrait": "Portraits/Won Gyun",
        "text": "적선이 바다를 덮었소. 전라좌수사는 어서 함대를 이끌고 구원하러 오시오.",
        "choices": [ {"text": "계속", "uniques": ["Triggers a [Briefing Decision] event"]} ]
    },
    {
        "name": "Briefing Decision",
        "speaker": "이순신",
        "portrait": "Portraits/Yi Sun-sin",
        "text": "경상도 바다는 우리 관할이 아니나 사세가 급하다. 전라우수사 이억기의 함대를 기다려 함께 나갈 것인가, 지금 바로 나갈 것인가.",
        "choices": [
            {"text": "지금 바로 출전한다", "uniques": ["Instantly provides [1] [Popular Support]"]},
            {"text": "이억기의 전라우수영 함대를 기다린다", "uniques": ["[2] free [Panokseon] units appear", "Instantly provides [1] [Waited For Yi Eok-gi] <hidden from users>", "Comment [기다린 만큼 이 장의 제한 시간이 4턴 줄어듭니다]"]}
        ]
    },
    {
        "name": "Okpo Speech",
        "speaker": "이순신",
        "portrait": "Portraits/Yi Sun-sin",
        "text": "가볍게 움직이지 말라. 침착하게, 산처럼 무겁게 행동하라.",
        "civilopediaText": [ {"extraImage": "Scenes/Battle of Okpo", "imageSize": 480, "centered": true} ],
        "choices": [ {"text": "전군, 옥포의 적을 쳐라"} ]
    },
    {
        "name": "Sacheon Sortie",
        "civilopediaText": [
            {"extraImage": "Scenes/Turtle Ship Sortie", "imageSize": 480, "centered": true},
            {"header": 3, "text": "1592년 5월 29일, 사천"},
            {"text": "거북선이 처음으로 적진 한가운데로 뛰어들었다. 연기를 뿜는 용머리 아래에서 왜선들이 길을 잃었다."},
            {"text": "이 싸움에서 이순신은 왼쪽 어깨에 총탄을 맞았으나, 싸움이 끝날 때까지 내색하지 않았다."}
        ],
        "choices": [ {"text": "거북선, 돌격하라", "uniques": ["Free [Turtle Ship] appears"]} ]
    },
    {
        "name": "Yi Fallen",
        "civilopediaText": [ {"text": "이순신의 대장선이 침몰했다. 지휘를 잃은 함대는 흩어지고, 남해의 바닷길이 왜군에게 열렸다."} ],
        "choices": [ {"text": "물러난다"} ]
    },
    {
        "name": "Chapter 1 Timeout",
        "civilopediaText": [ {"text": "때를 놓쳤다. 왜군 수송선단이 남해를 돌아 서해로 나아가고, 평양의 왜군에게 군량과 증원이 닿기 시작했다."} ],
        "choices": [ {"text": "물러난다"} ]
    }
]
```

- [ ] **Step 4: 본영 건물과 유닛에 대본 연결**

`Buildings.json`을 다음으로 바꾼다:
```json
[
    {
        "name": "Chapter 1 HQ",
        "cost": 0,
        "uniques": [
            "Unbuildable",
            "Will not be displayed in Civilopedia",
            "Triggers a [Yi Fallen] event <upon turn start> <when number of [[Yi Sun-sin] Units] is equal to [0]> <when number of [Defeat Flag] is equal to [0]>",
            "Instantly provides [1] [Defeat Flag] <upon turn start> <when number of [[Yi Sun-sin] Units] is equal to [0]>",
            "Triggers a [Chapter 1 Timeout] event <upon turn start> <after turn number [40]> <when number of [Defeat Flag] is equal to [0]>",
            "Instantly provides [1] [Defeat Flag] <upon turn start> <after turn number [40]>",
            "Triggers a [Chapter 1 Timeout] event <upon turn start> <after turn number [36]> <when number of [Waited For Yi Eok-gi] is more than [0]> <when number of [Defeat Flag] is equal to [0]>",
            "Instantly provides [1] [Defeat Flag] <upon turn start> <after turn number [36]> <when number of [Waited For Yi Eok-gi] is more than [0]>"
        ]
    },
    {
        "name": "Japanese Command Ch1",
        "cost": 0,
        "uniques": [
            "Unbuildable",
            "Will not be displayed in Civilopedia",
            "[2] free [Sekibune] units appear <upon turn start> <every [6] turns>"
        ]
    }
]
```

`Units.json`에서 `Panokseon`, `Turtle Ship`, `Yi Sun-sin`의 `uniques` 배열 끝에 다음 한 줄을 추가한다:
```json
"Instantly provides [1] [Ships Sunk] <upon defeating a [Water] unit>"
```
`Yi Sun-sin`의 `uniques` 끝에는 다음 네 줄도 추가한다:
```json
"Triggers a [Okpo Speech] event <upon entering a [Okpo Waters] tile> <when number of [Okpo Speech Seen] is equal to [0]>",
"Instantly provides [1] [Okpo Speech Seen] <upon entering a [Okpo Waters] tile> <when number of [Okpo Speech Seen] is equal to [0]>",
"Triggers a [Sacheon Sortie] event <upon entering a [Sacheon Waters] tile> <when number of [Sacheon Event Seen] is equal to [0]>",
"Instantly provides [1] [Sacheon Event Seen] <upon entering a [Sacheon Waters] tile> <when number of [Sacheon Event Seen] is equal to [0]>"
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.campaign.*"`
Expected: 모든 campaign 테스트 PASS(`ImjinModTest` 포함, 경고 0).

알려진 위험과 대응:
- **`losingYiSunSinLosesTheChapter` 또는 `runningOutOfTimeLosesTheChapter`에서 이벤트가 2번 뜬다.**
  - 원인: 도시 문맥에서 `[Defeat Flag]`가 문명 비축량이 아니라 도시 값으로 읽히는 경우다(`CityResources.kt:86-88` 확인).
  - 대응: 조건을 `<when number of [[Defeat Flag] resource of [Joseon] Civilizations] is equal to [0]>`으로 바꾼다.
- **`okpoSpeechPlaysOnlyOnce`에서 2번 뜬다.** 같은 방식으로 유닛 쪽 조건을 바꾼다.
- **`sacheonSortieLaunchesTheTurtleShip`에서 거북선이 여수에 생긴다.** 테스트는 통과한다. 작업 8 플레이 테스트에서 위치가 어색하면 기록한다.
- **`sinkingAShipCountsTowardsVictory`에서 공격이 안 일어난다.** `placeUnitNearTile`이 인접 칸에 놓지 못한 경우다. 수송선 인접 연안 칸을 골라 `MapUnit.putInTile`로 직접 놓는다.

- [ ] **Step 6: 시나리오 재생성**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:buildScenarios`
Expected: `BUILD SUCCESSFUL`

- [ ] **Step 7: 커밋**

```powershell
git add "campaign/Imjin War 1592/jsons" "campaign/Imjin War 1592/scenarios" campaign/tools/src/com/unciv/campaign/Chapter1ScriptTest.kt
git commit -m "Imjin War chapter 1: prologue, briefing, battle events, and defeat conditions" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### 작업 7: 아트

**Files:**
- Create: `campaign/tools/art/postprocess.py`
- Create (원본, git 제외): `campaign/art-src/{portraits,leaders,scenes,units,nations}/*.png`
- Create (결과):
  - `campaign/Imjin War 1592/ExtraImages/Portraits/*.png`
  - `campaign/Imjin War 1592/ExtraImages/Scenes/*.png`
  - `campaign/Imjin War 1592/Images/LeaderIcons/*.png`
  - `campaign/Imjin War 1592/Images/UnitIcons/*.png`
  - `campaign/Imjin War 1592/Images/NationIcons/*.png`
- Modify: `.gitignore` (`campaign/art-src/` 추가)

**Interfaces:**
- Consumes: 작업 6의 `portrait`/`extraImage` 이름, 작업 3의 유닛·문명·지도자 이름. 파일 이름이 정확히 같아야 한다.

**규격:**

| 종류 | 파일 이름 (확장자 .png) | 결과 크기 |
|---|---|---|
| 초상화 | `Seonjo`, `Ryu Seong-ryong`, `Yi Sun-sin`, `Won Gyun`, `Yi Eok-gi`, `Hwang Yun-gil`, `Kim Seong-il`, `Toyotomi Hideyoshi` | 512×512 |
| 지도자 | `Seonjo`, `Toyotomi Hideyoshi`, `Wanli Emperor` | 256×256 |
| 장면 | `Busan Falls`, `Battle of Okpo`, `Turtle Ship Sortie` | 960×540 |
| 유닛 아이콘 | `Panokseon`, `Yi Sun-sin`, `Atakebune`, `Sekibune`, `Japanese Transport` | 100×100, 투명 배경 흰 실루엣 |
| 문명 아이콘 | `Joseon`, `Toyotomi`, `Ming` | 100×100, 투명 배경 흰 문양 |

- [ ] **Step 1: 원본 폴더를 git에서 제외**

`.gitignore` 끝에 추가:
```gitignore
# Imjin War campaign: raw generated art (only the processed images in the mod folder are committed)
campaign/art-src/
```

- [ ] **Step 2: 후처리 스크립트 작성**

`campaign/tools/art/postprocess.py`:
```python
"""Turn generated art into the sizes Unciv uses. Run from the repo root:
    python campaign/tools/art/postprocess.py
Reads campaign/art-src/<kind>/*.png and writes into the mod folder with the same file names."""
from pathlib import Path
from PIL import Image, ImageOps

CAMPAIGN = Path(__file__).resolve().parents[2]
SRC = CAMPAIGN / "art-src"
MOD = CAMPAIGN / "Imjin War 1592"


def square(img, size):
    # Faces sit in the upper part of a bust portrait, so crop a little above center
    return ImageOps.fit(img.convert("RGB"), (size, size), Image.LANCZOS, centering=(0.5, 0.35))


def wide(img):
    return ImageOps.fit(img.convert("RGB"), (960, 540), Image.LANCZOS)


def silhouette(img, size=100, margin=6):
    """Black-on-white drawing -> white shape on transparent background, as Unciv icons are"""
    alpha = ImageOps.invert(img.convert("L"))
    alpha = alpha.point(lambda v: 0 if v < 40 else v)  # drop paper noise
    alpha = alpha.crop(alpha.getbbox())
    alpha.thumbnail((size - 2 * margin, size - 2 * margin), Image.LANCZOS)
    shape = Image.new("RGBA", alpha.size, (255, 255, 255, 255))
    shape.putalpha(alpha)
    out = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    out.paste(shape, ((size - alpha.width) // 2, (size - alpha.height) // 2), shape)
    return out


JOBS = [
    ("portraits", MOD / "ExtraImages" / "Portraits", lambda i: square(i, 512)),
    ("leaders", MOD / "Images" / "LeaderIcons", lambda i: square(i, 256)),
    ("scenes", MOD / "ExtraImages" / "Scenes", wide),
    ("units", MOD / "Images" / "UnitIcons", silhouette),
    ("nations", MOD / "Images" / "NationIcons", silhouette),
]

for kind, dest, convert in JOBS:
    folder = SRC / kind
    if not folder.exists():
        continue
    dest.mkdir(parents=True, exist_ok=True)
    for src in sorted(folder.glob("*.png")):
        convert(Image.open(src)).save(dest / src.name)
        print(f"{kind}: {src.name}")
```

- [ ] **Step 3: 화풍 기준 이미지 1장 생성 후 사용자 확인 (사람 확인 관문)**

`codex-jjap-mcp` 스킬을 먼저 불러 사용법을 확인한다. 그다음 GPT 이미지 도구로 아래 프롬프트의 이순신 초상화를 정사각형으로 만들어 `campaign/art-src/portraits/Yi Sun-sin.png`에 저장한다.

모든 프롬프트 앞에 붙이는 공통 화풍 문구:
```text
Korean traditional color painting (chaesaekhwa) style, semi-realistic illustration, Joseon dynasty 1590s, muted mineral pigments on hanji paper texture, soft ink outlines, dignified composition, no text, no letters, no watermark.
```
이순신:
```text
Bust portrait of Admiral Yi Sun-sin, Joseon naval commander in his late 40s, stern calm face, thin beard, wearing Joseon military officer armor with a helmet, deep red and black colors, three-quarter view, plain dark background, square image.
```
생성한 이미지를 사용자에게 보여주고(`SendUserFile`) 화풍을 승인받는다. **승인 전에는 Step 4로 넘어가지 않는다.** 수정 요청이 오면 공통 화풍 문구를 고쳐 다시 만든다. 이후 모든 이미지에 그 문구를 그대로 쓴다.

- [ ] **Step 4: 나머지 초상화와 지도자 이미지 생성**

공통 화풍 문구 + 아래 문구로 각각 만들어 `campaign/art-src/portraits/<파일 이름>.png`에 저장한다. 모두 끝에 `three-quarter view, plain dark background, square image.`를 붙인다.

| 파일 이름 | 프롬프트 |
|---|---|
| `Seonjo` | Bust portrait of King Seonjo of Joseon, about 40 years old, red royal robe with a gold dragon roundel, black ikseongwan crown, troubled expression |
| `Ryu Seong-ryong` | Bust portrait of prime minister Ryu Seong-ryong, Joseon scholar-official in his 50s, dark red official robe with a crane rank badge, black samo hat, thoughtful expression |
| `Won Gyun` | Bust portrait of Joseon admiral Won Gyun, burly man in his 50s, Joseon armor, agitated shouting expression |
| `Yi Eok-gi` | Bust portrait of young Joseon admiral Yi Eok-gi in his early 30s, Joseon armor and helmet, determined expression |
| `Hwang Yun-gil` | Bust portrait of Joseon envoy Hwang Yun-gil, scholar-official in his 50s, dark blue official robe, black gat hat, grave worried expression |
| `Kim Seong-il` | Bust portrait of Joseon envoy Kim Seong-il, scholar-official in his 50s, dark green official robe, black gat hat, confident dismissive expression |
| `Toyotomi Hideyoshi` | Bust portrait of Japanese regent Toyotomi Hideyoshi, small thin man in his 50s, elaborate dark kimono and black eboshi hat, sharp ambitious eyes |

지도자 이미지:
- `portraits/Seonjo.png`와 `portraits/Toyotomi Hideyoshi.png`를 `campaign/art-src/leaders/`에 같은 이름으로 복사한다.
- `Wanli Emperor`는 새로 만들어 `campaign/art-src/leaders/Wanli Emperor.png`에 저장한다. 프롬프트: `Bust portrait of the Ming dynasty Wanli Emperor, about 30 years old, yellow imperial dragon robe, black winged crown, aloof expression`

- [ ] **Step 5: 장면 삽화 생성**

공통 화풍 문구 + 아래 문구로 가로 16:9 이미지를 만들어 `campaign/art-src/scenes/<파일 이름>.png`에 저장한다.

| 파일 이름 | 프롬프트 |
|---|---|
| `Busan Falls` | Wide scene, a Japanese invasion fleet of hundreds of ships landing at Busan harbor in 1592, smoke rising from the Busanjin fortress walls, defenders on the walls, dawn light, wide 16:9 image |
| `Battle of Okpo` | Wide scene, Joseon panokseon warships in a line firing cannons at burning Japanese ships in Okpo bay, hills of Geoje island behind, 1592, wide 16:9 image |
| `Turtle Ship Sortie` | Wide scene, a Korean turtle ship with a dragon head breathing smoke and a spiked roof charging into Japanese ships at Sacheon, splashing waves, wide 16:9 image |

- [ ] **Step 6: 아이콘 생성**

아이콘은 공통 화풍 문구를 쓰지 않는다. 아래 틀에 대상만 바꿔 정사각형으로 만들고 `campaign/art-src/units/` 또는 `campaign/art-src/nations/`에 저장한다:
```text
A single solid black silhouette of {대상}, centered, flat, no inner details, pure white background, simple game icon, square image.
```

| 폴더/파일 이름 | 대상 |
|---|---|
| `units/Panokseon` | a Korean panokseon warship seen from the side, a flat-bottomed two-deck ship with a raised fortified upper deck and oars |
| `units/Yi Sun-sin` | a helmeted Joseon admiral, head and shoulders in profile |
| `units/Atakebune` | a large Japanese atakebune warship seen from the side, with a tall wooden castle tower |
| `units/Sekibune` | a sleek Japanese sekibune war boat seen from the side, with many oars |
| `units/Japanese Transport` | a small Japanese sailing cargo boat seen from the side, with one square sail |
| `nations/Joseon` | a taegeuk yin-yang swirl inside a circle |
| `nations/Toyotomi` | the Toyotomi clan paulownia crest (go-shichi no kiri mon) |
| `nations/Ming` | the Chinese character 明 written in a bold brush style |

- [ ] **Step 7: 후처리와 확인**

Run: `python campaign/tools/art/postprocess.py`
Expected: 종류별로 파일 이름이 출력된다. 합계 초상화 8, 지도자 3, 장면 3, 유닛 5, 문명 3.

아이콘 몇 개를 Read 도구로 열어 투명 배경 위 흰 실루엣인지 확인한다. 실루엣이 깨졌으면 원본을 다시 만든다. 배경 노이즈 탓이면 `silhouette()`의 임계값 40을 조정한다.

- [ ] **Step 8: 커밋**

```powershell
git add .gitignore campaign/tools/art/postprocess.py "campaign/Imjin War 1592/ExtraImages" "campaign/Imjin War 1592/Images"
git commit -m "Imjin War mod: portraits, scenes, leader, unit and nation art" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### 작업 8: 스모크 테스트, 통플레이, 밸런스

**Files:**
- Test: `campaign/tools/src/com/unciv/campaign/Chapter1SmokeTest.kt`
- Create: `campaign/docs/playtest-ch1.md`
- Modify (조정 시): `campaign/Imjin War 1592/jsons/Units.json`, `VictoryTypes.json`, `Buildings.json`, `campaign/tools/src/com/unciv/campaign/Chapter1.kt`

- [ ] **Step 1: AI 턴 스모크 테스트 작성과 실행**

`campaign/tools/src/com/unciv/campaign/Chapter1SmokeTest.kt`:
```kotlin
package com.unciv.campaign

import com.unciv.UncivGame
import com.unciv.testing.GdxTestRunner
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(GdxTestRunner::class)
class Chapter1SmokeTest {
    /** The human never moves, so Japan's AI gets to act for 15 rounds: no trigger, event, or AI path may crash */
    @Test
    fun fifteenTurnsRunWithoutErrors() {
        CampaignEnvironment.init()
        val game = Chapter1.build()
        UncivGame.Current.gameInfo = game
        repeat(15) { game.nextTurn() }
        assertTrue(game.turns >= 15)
        assertTrue(game.getCivilization("Joseon").isAlive())
    }
}
```
Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test --tests "com.unciv.campaign.Chapter1SmokeTest"`
Expected: PASS. 예외가 나면 스택 트레이스의 원인을 고친다(대부분 JSON 유니크나 배치 문제다). 사람 플레이어는 움직이지 않으므로 조선이 도시를 잃어도 이 테스트는 그 자체로 실패가 아니다. 다만 15턴 안에 조선이 멸망하면 일본 지상군이 너무 강한 것이다. 플레이 기록에 남긴다.

- [ ] **Step 2: 게임 실행**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat desktop:run`
Expected: 게임 창이 뜬다. 첫 실행 시 모드 이미지가 아틀라스로 패킹된다.

- [ ] **Step 3: 통플레이 확인 (사람 또는 computer-use)**

화면을 볼 수 있는 사용자에게 아래 목록대로 플레이를 요청한다. 또는 `anthropic-skills:computer-use` 스킬로 직접 진행한다. 결과는 항목마다 통과/실패와 메모로 `campaign/docs/playtest-ch1.md`에 기록한다.

1. 설정 → 언어 한국어. 새 게임 → 맵 종류 "시나리오" → "임진왜란 1장 「바다를 지켜라」"가 목록에 있다.
2. 플레이어 목록에 조선이 사람으로 고정돼 있고, AI 토글과 문명 변경이 막혀 있다(패치 1).
3. 시작하자마자 통신사 프롤로그가 뜨고, 황윤길·김성일·선조·류성룡 대사에 초상화와 이름이 보인다(패치 2).
4. 상단 연도가 1592년이다.
5. 선택지 아래에 효과(판옥선, 금, 거북선 등)가 표시되고, 고른 대로 유닛이 생긴다.
6. 부산 함락 장면 삽화와 원균·이순신 대사가 이어진다. "기다린다"를 고르면 판옥선 2척과 제한 시간 안내가 나온다.
7. 이순신을 옥포 앞바다로 옮기면 연설이 한 번만 뜨고, 사천 앞바다에서 거북선 출전 장면이 뜬다.
8. 타일 정보에 "옥포 앞바다"가 보이고, 맵에는 해역 표시가 그려지지 않는다.
9. 일본 함선 12척을 격침하면 승리 화면에 "바다를 지켜냈다"와 2장 예고가 나온다.
10. 새로 시작해 이순신을 일부러 잃으면 다음 턴에 "Yi Fallen" 이벤트가 뜨고, 일본 턴이 끝난 뒤 패배 화면에 "남해의 바닷길이 왜군에게 열렸다" 문구가 나온다.
11. 외교 화면에서 선조·도요토미 지도자 초상화, 도시 배너에 문명 아이콘, 유닛 목록에 판옥선·아타케부네 아이콘이 보인다.

- [ ] **Step 4: 밸런스 조정**

플레이 기록을 보고 아래만 조정한다. 조정할 때마다 `.\gradlew.bat :tests:buildScenarios`로 다시 생성하고, `.\gradlew.bat :tests:test --tests "com.unciv.campaign.*"`로 테스트를 돌린다.
- 승리 격침 수 12: `VictoryTypes.json`. 바꾸면 `Chapter1ScenarioTest.sinkingTwelveShipsWinsTheChapter`의 11/12도 같이 바꾼다.
- 제한 턴 40/36: `Buildings.json`. 바꾸면 `Chapter1ScriptTest`의 39/40/36도 같이 바꾼다.
- 함선 전투력: `Units.json`
- 일본 함대 배치·증원 주기: `Chapter1.kt`, `Buildings.json`. 바꾸면 `castCitiesAndFleetsArePlaced`의 17, `japanReinforcesBusanEverySixTurns`도 같이 바꾼다.

목표는 처음 하는 플레이어가 제한 턴의 3분의 2 안에 이길 수 있고, 이순신을 무리하게 앞세우면 질 수 있는 정도다.

- [ ] **Step 5: 전체 테스트와 커밋**

Run: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'; .\gradlew.bat :tests:test`
Expected: `BUILD SUCCESSFUL`.

```powershell
git add campaign
git commit -m "Imjin War chapter 1: smoke test, playtest notes, and balance" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

---

## 자체 점검 결과

- **설계 문서 대응:**
  - 패치 1: 작업 1. 패치 2: 작업 2. 패치 3: 범위 밖(2단계).
  - 모드 구조: 작업 3. 스크립트 방식: 작업 6. 패배 처리: 작업 5, 6.
  - 1장: 작업 5, 6. 시나리오 빌드 도구: 작업 4, 5. 아트: 작업 7.
  - 언어: 작업 3, 6. 검증: 각 작업의 테스트와 작업 8.
- **범위 밖 항목**(설계 문서 11절)은 다루지 않는다.
- **이름 일관성:** 작업 3의 ID 목록을 작업 4~8이 그대로 쓴다. `Chapter1`의 상수(`VICTORY`, `JAPANESE_VICTORY`, `OPENING_EVENT`, `HQ`, `JAPANESE_HQ`)는 작업 5에서 정의하고 작업 6, 8이 쓴다.
