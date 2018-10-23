---
layout: post
title: 안드로이드 앱의 Persistent data를 제대로 암호화해 보자! (1/2)
date: 2018-06-03
author: hwan
published: true
excerpt: 안드로이드에서 좀 더 안전하게 파일 시스템에 데이터를 저장하는 방식을 소개합니다
tags: android tip kotlin cipher security
---
## 들어가기
오늘 소개해드릴 글은 안드로이드에서 좀 더 안전하게 파일 시스템에 데이터를 저장하는 방식에 관한 내용입니다. 이 글은 중급 이상, 상급 이하 안드로이드 개발자를 대상으로 작성했으며 완독하는데 약 20분 정도가 필요합니다. 최대한 쉽게 쓰려고 노력했습니다만 이 글이 잘 이해되지 않는 독자분들은 이 문서 말미의 [더 보기](#더-보기) 섹션에 링크된 외부 문서들을 읽어보시는 편이 좋습니다.

1부에서는 Shared preferences 에 저장하는 데이터를 암호화 하는 방식에 대해 다루고 있으며, 2부에서는 데이터베이스를 암호화 하는 방식에 대해 다루겠습니다.

## 내 앱의 데이터, 과연 유출로부터 안전할까?
안드로이드 공식 사이트의 [저장소 개발 가이드 문서](https://developer.android.com/guide/topics/data/data-storage)는 데이터를 저장하는 여러 가지 방법을 소개하고 있습니다. 그 중 '내부 저장소' 의 다음 특징은 눈여겨볼 만 합니다.

> 기기의 내부 저장소에 파일을 직접 저장할 수 있습니다. 기본적으로, **내부 저장소에 저장된 파일**은 해당 애플리케이션의 전용 파일이며 **다른 애플리케이션(및 사용자)은 해당 파일에 액세스할 수 없습니다**. 사용자가 애플리케이션을 제거하면 해당 캐시 파일은 제거됩니다.

즉, 다른 애플리케이션에 노출하면 곤란한 중요한 정보들은 내부 저장소에 담아두면 안전하다고 할 수 있습니다. 하지만, 정말일까요? 다음 예제를 이용해 내부 저장소에 저장한 사용자의 중요한 정보를 어떻게 탈취하는지 알아보겠습니다. 예제 앱은 충성 사용자에게 보상하기 위해 사용자가 앱을 몇 번 실행시켰는지를 기록합니다.

```kotlin
class AppRanTimesRecordingActivity : AppCompatActivity() {
    private val sharedPrefs by lazy {
        // Shared preferences 는 Internal storage 에 저장된다.
        getSharedPreferences(SHARED_PREF_NAME, Context.MODE_PRIVATE)
    }
    private var appRanCount = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        accessToSharedPrefs()
        appRanCount++

        Toast.makeText(applicationContext, "App has ran $appRanCount times!!", Toast.LENGTH_LONG).show()
        finish()
    }

    override fun onDestroy() {
        saveSharedPrefs()
        super.onDestroy()
    }

    private fun accessToSharedPrefs() {
        sharedPrefs.run { appRanCount = getInt(KEY_APP_RAN_COUNT, 0) }
    }

    private fun saveSharedPrefs() {
        sharedPrefs.edit().run({
            putInt(KEY_APP_RAN_COUNT, appRanCount)
            apply()
        })
    }

    companion object {
        private const val SHARED_PREF_NAME = "MySecureSettings"

        private const val KEY_APP_RAN_COUNT = "appRanCount"
    }
}
```
**\[리스트 1\]** MODE_PRIVATE 로 보호하는 SharedPreferences 사용

앱의 데이터는 `/data/data/com.securecompany.secureapp` 에 저장되어 있습니다만, 앱을 release 모드로 빌드하면 `adb` 명령으로도 볼 수 없으니 안전하다고 할 수 있을 겁니다. 실제로 `adb` 명령을 이용해 저장한 파일을 보려고 시도하면 아래와 같은 오류가 발생합니다.

```shell
$ adb shell "run-as com.securecompany.secureapp ls -al /data/data/com.securecompany.secureapp"
run-as: Package 'com.securecompany.secureapp' is not debuggable
```

그렇다면 디버거로도 볼 수 없으니 내부 저장소에 저장한 데이터가 안전하다고 말 할 수 있을까요?

**그렇지 않습니다!** 안드로이드는 루팅이 매우 손쉬운 운영체제기 때문에 설령 release 모드로 빌드한 앱이라 하더라도 `adb` 명령을 이용해 모두 접근할 수 있습니다. 루팅한 기기에서 우리가 제작한 SecureApp의 내부 저장소 구조를 아래와 같이 확인할 수 있습니다.

```shell
$ adb shell "sudo ls -al /data/data/com.securecompany.secureapp"
drwxrwx--x u0_a431  u0_a431           2018-06-04 14:15 cache
drwxrwx--x u0_a431  u0_a431           2018-06-04 14:15 code_cache
drwxrwx--x u0_a431  u0_a431           2018-06-04 14:15 shared_prefs

$ adb shell "sudo ls -al /data/data/com.securecompany.secureapp/shared_prefs"
-rw-rw---- u0_a431  u0_a431       111 2018-06-04 14:15 MySecureSettings.xml

$ adb shell "sudo cat /data/data/com.securecompany.secureapp/shared_prefs/MySecureSettings.xml"
<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <int name="appRanCount" value="2" />
</map>
```

별다른 테크닉이 없더라도 인터넷에 널린 수많은 루팅 방법으로 기기를 루팅하면 제아무리 내부 저장소에 저장한 데이터라도 이렇게 손 쉽게 유출이 가능하다는 것을 확인할 수 있습니다. 이런 방식의 보안 기법은 [불투명성에 의지한 보안](https://en.wikipedia.org/wiki/Security_through_obscurity)이라고 하여, 방법을 전혀 모르는 공격자에게는 유효한 방식입니다만 이 글을 읽는 독자 수준의 개발자라면 취약점을 금세 파악할 수 있다는 단점이 있습니다.

## 그렇다면 암호화를 적용하면 되지 않을까?
맞습니다. 어차피 유출을 피할 수 없다면, 데이터를 암호화하면 됩니다. 그래서 암호화 로직으로 데이터를 암호화해 보도록 하겠습니다. 이 코드는 AES / CBC / PKCS5Padding 방식을 사용해 주어진 데이터를 암호화합니다. 각 용어를 간략하게 설명하자면 다음과 같습니다.

- AES: 미국에서 개발된 블럭 암호화 방식으로 좀 더 나은 보안성을 가진다. 데이터를 일정 크기(블럭)로 나눠 암호화하며 보통 128비트, 192비트, 256비트 단위로 암호화한다. 키의 길이는 암호화 방식에서 사용할 블럭 크기와 완전히 같아야 하는 특징이 있다.
- CBC: 블럭을 회전시키는 방식을 말한다. 최초로 소개된 블럭 회전 알고리즘인 ECB(Electronic Code Book) 의 보안 취약점을 해결하기 위한 방식으로 같은 데이터 입력에 대해 완전히 다른 결과를 내므로 보안성이 좀 더 높다. 하지만 CBC 방식을 위해서는 초기화 벡터(Initialisation Vector, IV)를 반드시 사용해야 한다.
- IV : CBC 블럭 회전방식에 사용하는 초기화 값. 암호화할 데이터와 키가 변하지 않더라도 이 값만 바뀌면 결과가 크게 달라진다. 암호화 key 와는 전혀 무관한 값이기 때문에 외부에 노출되더라도 보안 위협은 적은 편이며 암호화 요청마다 다른 IV 를 사용해 보안성을 높일 수 있다. 다만, 키 길이와 일치하는 길이의 IV 가 필요하다.
- PKCS5Padding: 블럭 암호화 방식은 입력 데이터의 길이가 블럭의 길이 혹은 그 배수와 일치해야 하는 문제점이 있다. 입력 데이터가 블럭 길이보다 짧을 경우 원칙적으로 암호화가 불가능하다. 이런 어이없는 단점을 보완하기 위한 방식으로, 입력 데이터를 강제로 블럭 크기만큼 맞춰주는 알고리즘의 일종이다.

```kotlin
object AESHelper {
    /** 키를 외부에 저장할 경우 유출 위험이 있으니까 소스 코드 내에 숨겨둔다. 길이는 16자여야 한다. */
    private const val SECRET_KEY = "HelloWorld!!@#$%"
    private const val CIPHER_TRANSFORMATION = "AES/CBC/PKCS5PADDING"

    fun encrypt(plainText: String, initVector: String): String {
        val cipherText = try {
            with(Cipher.getInstance(CIPHER_TRANSFORMATION), {
                init(Cipher.ENCRYPT_MODE, 
                        SecretKeySpec(SECRET_KEY.toByteArray(), "AES"), 
                        IvParameterSpec(initVector.toByteArray()))
                return@with doFinal(plainText.toByteArray())
            })
        } catch (e: GeneralSecurityException) {
            // 특정 국가 혹은 저사양 기기에서는 알고리즘 지원하지 않을 수 있음. 특히 중국/인도 대상 기기
            e.printStackTrace()
            ""
        }

        return Base64.encodeToString(cipherText, Base64.DEFAULT)
    }

    fun decrypt(base64CipherText: String, initVector: String): String {
        val plainTextBytes = try {
            with(Cipher.getInstance(CIPHER_TRANSFORMATION), {
                init(Cipher.DECRYPT_MODE,
                        SecretKeySpec(SECRET_KEY.toByteArray(), "AES"),
                        IvParameterSpec(initVector.toByteArray()))
                val cipherText = Base64.decode(base64CipherText, Base64.DEFAULT)
                return@with doFinal(cipherText)
            })
        } catch (e: GeneralSecurityException) {
            // 특정 국가 혹은 저사양 기기에서는 알고리즘 지원하지 않을 수 있음. 특히 중국/인도 대상 기기
            e.printStackTrace()
            ByteArray(0, { i -> 0 })
        }

        return String(plainTextBytes)
    }
}
```
**\[리스트 2\]** 간단히 구현한 AES128 암호 및 해독 로직

그리고 위의 AESHelper 를 이용해 SharedPreference 에 들어갈 자료를 암호화해 봅시다.

```kotlin
class MainActivity : AppCompatActivity() {
    private val iv by lazy { lazyInitIv() }
    private val sharedPrefs by lazy {
        getSharedPreferences(SHARED_PREF_NAME, Context.MODE_PRIVATE)
    }

    private var appRanCount = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Shared preferences 는 Internal storage 에 저장된다.
        accessToSharedPrefs()
        appRanCount++

        Toast.makeText(applicationContext, "App has ran $appRanCount times!!", Toast.LENGTH_LONG).show()
    }

    override fun onDestroy() {
        saveSharedPrefs()
        super.onDestroy()
    }

    private fun accessToSharedPrefs() {
        sharedPrefs.run({
            val appRanCntEncrypted = getString(KEY_APP_RAN_COUNT, "")
            if (appRanCntEncrypted.isEmpty()) {
                return@run
            }

            appRanCount = AESHelper.decrypt(appRanCntEncrypted, iv).toInt()
        })
    }

    private fun saveSharedPrefs() {
        sharedPrefs.edit().run({
            putString(KEY_APP_RAN_COUNT, AESHelper.encrypt(appRanCount.toString(), iv))
            apply()
        })
    }

    private fun lazyInitIv(): String {
        return sharedPrefs.run({
            var iv = getString(KEY_SESSION_IV, "")
            if (iv.isEmpty()) {
                // 2001년 - 2286년 동안에는 항상 13자리로 나타난다. 그러므로 16자리 IV가 보장된다.
                iv = "${System.currentTimeMillis()}000"
                edit()
                    .putString(KEY_SESSION_IV, iv)
                    .apply()
            }

            return@run iv
        })
    }

    companion object {
        private const val SHARED_PREF_NAME = "MySecureSettings"

        private const val KEY_APP_RAN_COUNT = "appRanCount"
        private const val KEY_SESSION_IV    = "ivForSession"
    }
}
```
**\[리스트 3\]** *리스트 2*를 활용해 데이터를 암호화해 저장.

저장한 SharedPreferences 를 확인해 보면 다음과 같은 결과를 얻을 수 있습니다.

```shell
$ adb shell "sudo cat /data/data/com.securecompany.secureapp/shared_prefs/MySecureSettings.xml"
<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="ivForSession">1528095873216000</string>
    <string name="appRanCount">F9dq8ezypMPeUsHpPIUcnQ==
    </string>
</map>
```

역시 기대대로 암호화되었네요. IV 는 노출돼도 상관없는 정보라고 했으니 괜찮겠죠. 이제 우리 앱의 사용자는 설령 기기를 잃어버리더라도 소중한 정보가 암호화되어 있으니 문제없을 겁니다.

**라고 생각한다면 오산입니다!** 불행히도 안드로이드는 디컴파일이 매우 쉬운 플랫폼이기 때문에 이런 식의 암호화는 사실 그다지 효과가 있지 않습니다. 심지어 IV 가 그대로 노출되어 있기 때문에 공격자에게 큰 힌트가 되었습니다. IV 는 키와는 다른 값이므로 유출되어도 상관없다곤 하지만, 어쨌든 암호화 과정에서 중요하게 다뤄지는 정보임에는 매한가지이므로 사용자에게 굳이 노출할 필요는 없습니다.

다소 극단적인 예를 들어 설명했습니다만 요지는 이렇습니다. 어떤 식으로든 우리의 로직 내에서 키를 관리하는 방식으로는 완벽하게 암호화했다고 말할 수 없습니다. AESHelper 소스의 첫 줄에 있는 내용을 다시 한번 살펴봅시다.

```kotlin
    /** 키를 외부에 저장할 경우 유출 위험이 있으니까 소스 코드내에 숨겨둔다. 길이는 16자여야 한다. */
    private const val SECRET_KEY = "HelloWorld!!@#$%"
```

불행히도 이 소스에 적힌 코멘트는 틀렸습니다. [jadx](https://github.com/skylot/jadx) 나 [bytecode-viewer](https://github.com/Konloch/bytecode-viewer) 로 획득한 우리 앱의 APK 파일을 디컴파일 해 봅시다.

```java
@Metadata(
   mv = {1, 1, 10},
   bv = {1, 0, 2},
   k = 1,
   d1 = {"\u0000\u0014\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0002\b\u0002\n\u0002\u0010\u000e\n\u0002\b\u0007\bÆ\u0002\u0018\u00002\u00020\u0001B\u0007\b\u0002¢\u0006\u0002\u0010\u0002J\u0016\u0010\u0006\u001a\u00020\u00042\u0006\u0010\u0007\u001a\u00020\u00042\u0006\u0010\b\u001a\u00020\u0004J\u0016\u0010\t\u001a\u00020\u00042\u0006\u0010\n\u001a\u00020\u00042\u0006\u0010\b\u001a\u00020\u0004R\u000e\u0010\u0003\u001a\u00020\u0004X\u0082T¢\u0006\u0002\n\u0000R\u000e\u0010\u0005\u001a\u00020\u0004X\u0082T¢\u0006\u0002\n\u0000¨\u0006\u000b"},
   d2 = {"Lcom/securecompany/secureapp/AESHelper;", "", "()V", "CIPHER_TRANSFORMATION", "", "SECRET_KEY", "decrypt", "base64CipherText", "initVector", "encrypt", "plainText", "production sources for module app"}
)
public final class zzw {
   private static final String A = "HelloWorld!!@#$%";
   private static final String B = "AES/CBC/PKCS5PADDING";
   public static final zzw INSTANCE;

   // ...
}
```
**\[리스트 4\]** *리스트 2*를 디컴파일한 결과. 키가 그대로 노출됨을 확인할 수 있다.

이름은 난독화했지만 문자열이 그대로 노출된 상태이므로 공격자가 단서를 찾기란 매우 쉬울 겁니다. 더군다나 원본 소스의 내용이 짧으니 아무리 난독화 했더라도 내용을 파악하기란 그리 어렵지도 않을 것이고요.

여기서 일부 독자분들은 '그럼 이 로직을 JNI 로 만들면 되지 않냐?' 라고 반문하실 수도 있습니다. 하지만 JNI 로 컴파일한 .so 파일조차 `objdump` 같은 명령으로 내용을 다 들춰볼 수 있습니다. 특히 Kotlin 구현처럼 `static const` 형태로 소스코드에 적어두면 공격자 입장에서는 [`.data` 세그먼트](https://en.wikipedia.org/wiki/Data_segment) 만 확인하면 되죠. 그렇다면 `.data` 세그먼트를 회피하기 위해 로직으로 키를 생성하도록 작성했다고 해 봅시다. 좀 더 난이도가 올라가긴 하겠지만 숙련된 공격자라면 `.text` 
세그먼트를 이 잡듯이 뒤져 실마리를 찾을 수 있을 겁니다. 물론 이 정도 수준의 역공학을 할 수 있는 사람의 수는 적지만, 아예 없지는 않으니 문제는 여전히 남아 있습니다. 한번 확인해 볼까요?

```cpp
static const char* SECRET_KEY = "HelloWorld!!@#$%"

void encrypt(char* plainText, char* initVector, char[] result)
{
    char* now = malloc(sizeof(char) * 13); 
    itoa(&time(NULL), now, 10);
    char* iv = malloc(sizeof(char) * 16);
    strcpy(iv, *now);
    strncpy(iv, "000", 3);

    const struct AES_ctx aesCtx = { .RoundKey = 16, .Iv = *iv }
    AES_init_ctx(aesCtx, SECRET_KEY);
    // ...
}
```
**\[리스트 5\]** C 로 작성한 AESHelper 로직(일부).

```shell
$ objdump "mySecureApp/build/obj/local/armeabi-v7a/libAESHelper.so"

section .data
    # 의미 불명의 문자열 발견! 혹시 key 는 아닐까???
    00000200 db "HelloWorld!!@#$%", 16
    00000210 equ $ - 00000200

section .text
    global _start
    _start:
    # ...
        mov rsi, 00000200  # 이 명령 앞뒤로 조사해보면 저 문자열의 용도를 파악할 수 있다.
        mov rdx, 00000210
        syscall
    # ...
```
**\[리스트 6\]** ARM EABI V7용으로 컴파일한 바이너리를 디스어셈블 한 결과.

즉, 어떤 방식으로 구현하건 암호화에 쓸 키를 소스 코드에 박아두는 것은 그다지 현명한 선택이 아니란 것입니다. 더군다나 안드로이드에서 앱을 만든다는 것은 내 로직이 공격자에게 낱낱이 까발려져 있다는 것을 의미합니다. 중요한 데이터를 `.text` 에 들어가도록 숨기는 것도 가능하긴 하지만, 그런 방식은 나중에 유지보수하는 사람에게도 골치 아플 겁니다. 소스 코드가 그만큼 어려워질 테니까요. 그리고 그런 방식으로 정보를 숨긴다 하더라도 최정예 크래커 집단, 예를 들어 국정원 같은 수준이라면 그 정도는 큰 어려움 없이 파훼 가능합니다.

꿈도 희망도 없는 상황처럼 보입니다만 다행히도 안드로이드는 이런 문제를 해결해 주는 [KeyStore API](https://developer.android.com/training/articles/keystore) 를 제공하고 있습니다.

## KeyStore 를 도입하자
[Android KeyStore 시스템](https://developer.android.com/training/articles/keystore) 문서의 첫 머리에 적혀있는 글은 다음과 같습니다.

> The Android Keystore system lets you store cryptographic keys in a container to make it more difficult to extract from the device. Once keys are in the keystore, they can be used for cryptographic operations with the key material remaining non-exportable. Moreover, it offers facilities to restrict when and how keys can be used, such as requiring user authentication for key use or restricting keys to be used only in certain cryptographic modes.

> Android Keystore 시스템은 암호화 키를 '컨테이너' 에 저장하도록 해 기기에서 키를 추출하기 더욱 어렵게 해 줍니다. 일단 키를 Keystore 에 저장하면 키를 추출 불가능한 상태로 암호화에 사용할 수 있습니다. 또한 Keystore 는 키 사용 시기와 방법(예: 사용자 인증 등의 상황)을 통제하고, 특정 암호화에서만 키를 사용하도록 허용하는 기능도 제공합니다.

좀더 쉽게 다시 설명하자면, 암호화에 쓸 키를 소스코드 내부 어딘가가 아니라, 시스템만이 접근 가능한 어딘가(컨테이너)에 저장해 문제를 해결해 준다는 뜻입니다. 여기서 키가 저장되는 '컨테이너' 는 기기별로 구현이 다를 수 있습니다만 핵심은 사용자 어플리케이션이 그 영역에 접근할 수 없다는 점입니다. 이 때문에 KeyStore 를 사용해서 키를 안전하게 저장할 수 있습니다.

또한 앱에서 등록한 KeyStore 는 앱 삭제 시 함께 제거되므로, 똑같은 package name 으로 앱을 덮어씌우는 등의 공격으로 키를 유출할 수도 없습니다. 이는 여러 앱에서 공유하는 KeyChain 과는 다른 특성이며 기능 활성화를 위한 별도의 입력이 필요 없다는 장점이 있습니다.

![keychain-dialogue]({{ "/assets/2018-06-03-android-secure-persistent-howto/android-dialogue-KeyChain.png" | absolute_url }})

**\[그림 1\]** KeyChain API 사용시 나타나는 시스템 다이얼로그. 어려운 용어가 난무하는 등 사용자 경험이 그다지 좋다고 말할 수 없다.

반면 Android M 이상에서는, [KeyGenParameterSpec.Builder#setUserAuthenticationRequired(boolean)](https://developer.android.com/reference/android/security/keystore/KeyGenParameterSpec.Builder#setUserAuthenticationRequired(boolean)) API 로 시스템 다이얼로그의 표시 유무를 제어할 수 있습니다.

## Secure SharedPreferences 구현하기
앞서 설명드렸던 KeyStore 를 사용해 SharedPreferences 의 내용을 암호화하는 로직입니다. 소스 코드의 길이가 꽤 길기에, github gist 링크로 대신합니다. 독자 여러분들을 위해 최대한 쉽고 간단한 형태로 구현했으므로 필요에 맞춰 커스터마이징 하는게 좋습니다.

[AndroidCipherHelper.kt](https://gist.github.com/FrancescoJo/b8280cff14f1254f2185a9c2e927565e) - KeyStore 에서 생성한 랜덤 패스워드를 이용해 입력받은 문자열을 암호화 하는 로직. IV 설정 등 귀찮은 작업을 피하기 위해 비대칭 암호화 알고리즘을 사용했다. 또한 암호화 및 복호화 과정에서 비대칭키의 Public key 로 암호화하고, Private key 로 해독하도록 구현했다. TEE 를 올바르게 구현한 기기(안드로이드 23 이상 + 메이저 하드웨어 제조사)에서 동작하는 한, 이 데이터의 내용이 유출되더라도 복호화는 오직 이 로직 내부에서만 할 수 있다.

[SecureSharedPreferences.kt](https://gist.github.com/FrancescoJo/8753a63e1c6888c5d07ceb552c98104c) - AndroidCipherHelper 가 문자열 위주로 암호화하므로, 모든 입력값을 문자 형태로 변환 후 입출력한다.

## 결과 확인
Secure SharedPreferences 를 실제로 구현한 뒤, 앱의 shared preferences 를 열어보면 아래와 같은 결과가 나타납니다.

```shell
$ adb shell "run-as com.securecompany.secureapp cat /data/data/com.securecompany.secureapp/shared_prefs/MySecureSettings.xml"
<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="ivForSession">oh+XL/vQqAdxNzFEkKVOfcZAkP7jh92tcKpxzM6bbv9iGUk2lR7ayJsR6FZXt3rAKC+4sLVTP1cy
e+NpgZ67wjoeBM4maMjXjSkovc8cO8rVVsQLqedJtW3gGOItTTCkjIQGh+TsBDjz8C3IdmNSKqGE
GmBwQBoV0QuO+uO6cdPI/Gx816P0kcLmr5xsAy9XUwJeTE9947sYydiztJsgkKxuiGFLJK435pAb
UhatjSFse4MpBCugHcLUVg5UXGwQcfbJuuQ/CBcmQmYb3MldNzLfOWtsQiwQJpz0J12fsYlQOBnO
UnLVcND+DU17cP+Q4Cjah8VwmiY1a0shMn09Rw==
    </string>
    <string name="appRanCount">ozh8dKH+yCRSWoiW0HQtF/bWD7Aw6rfjzklT302AlTOpYmVdEiIfVoTK97bsyK1mXbwN5Qpas82Q
dYgnnZl9sfY8pzyXHM0dtm88euB5vgmzljb04LClF3oRZ7Qi5ZRyK90kQ/HN/6EgYvf6zEwR7Ydg
08kJ/bde4Z5lSz+kJ79dHEpE+QAV48U0F0/yp12+xKFRNbaBLBaaWclUNF10jONPKjC3HS/aQozT
1ngQWSKzPq87B0OFExraSPDoLT8zx8ElhTgEtpBRcUwtzmSnhGvgtIUhziFpZBbdvuqAGZ+L5El1
T7H9ipEosN3Aivh/5rz9dntJe3mJvfCFdFITlA==
    </string>
</map>
```

(Android L 이상이라고 가정할 경우)앱의 개발자조차 키를 알 수 없기 때문에, 파일을 유출하더라도 이를 깨는것은 현재로선 매우 어렵습니다. 즉, **우리 앱은 사용자 데이터를 안전하게 보호하고 있다**고 자신 있게 말할 수 있습니다.

## AndroidKeyStore 파헤쳐보기
그렇다면 어떤 방식으로 AndroidKeyStore 가 동작하고, 왜 안전한지 좀더 상세히 살펴보겠습니다. 

### "AndroidKeyStore" 문자열의 중요성
[Android Keystore system](https://developer.android.com/training/articles/keystore) 문서에 따르면 Android Keystore Service 에 접근하기 위해서는 아래와 같이 코드를 작성해야 한다고 합니다.

```kotlin
   val keyStore = java.security.KeyStore.getInstance("AndroidKeyStore")
```
**\[리스트 7\]** Android Keystore 인스턴스 획득 방법

여기서 주의할 점은 `AndroidKeyStore` 라는 문자열입니다. 반드시 정확한 문자열로 입력해야 합니다. 왜냐면 이는 Google 이 안드로이드의 보안 시스템을 Java Cryptography Architecture(JCA) 표준에 맞춰 구현했기 때문에 그렇습니다. 그리고 JCA 표준을 구현하면 JVM 인스턴스(안드로이드도 변형 JVM 의 일종입니다) 내에서 동작하는 모든 로직이 Security 클래스에 등록된 암호화 구현체를 사용할 수 있게 됩니다. 즉, Google 이 컨트롤 할 수 없는 서드파티 로직(우리의 앱 혹은 각종 안드로이드 오픈 소스들)에서도 Android Keystore 를 표준 Java 방식으로 사용할 수 있도록 구현했기에 이런 방식으로 호출해야 하는 겁니다.

물론 안드로이드에서는 AIDL 파일을 제공받는 방식 혹은 `Context#getSystemService(String)` 메소드로 서비스 인스턴스를 획득할 수도 있습니다. 하지만 첫 번째 방식은 바인드된 서비스가 언제든 Kill 될 수 있다는 문제가 있습니다. 그리고 두 방식의 공통적인 문제점은 보안을 사용하는 모든 로직에 `if (currentEnvironment == "Android") then...` 같은 예외 처리 로직을 넣어줘야 한다는 점입니다. 전 세계 모든 오픈소스 개발자들이 안드로이드로의 포팅을 위해 그런 귀찮은 작업을 해 줘야 하는 일인데.. 그게 가능할까요?

### "AndroidKeyStore" JCA Provider 등록 과정
앞서 `AndroidKeyStore` 라는 문자열의 중요성을 알아봤습니다. 그렇다면 왜 중요한지도 알아두면 좋겠죠?

안드로이드는 linux 기반의 운영체제입니다. 시스템 부팅 직후 실행되는 `init.rc` 스크립트에서는 [`/system/bin/app_process`](https://github.com/aosp-mirror/platform_frameworks_base/blob/master/cmds/app_process/app_main.cpp#L336) 명령을 실행하는데 이 명령은 [Android Runtime](https://github.com/aosp-mirror/platform_frameworks_base/blob/master/core/jni/AndroidRuntime.cpp#L1021) 위에서 실행되는 Zygote process를 [초기화](https://github.com/aosp-mirror/platform_frameworks_base/blob/master/core/java/com/android/internal/os/ZygoteInit.java#L217) 합니다.

Zygote 는 간단하게 설명하자면 안드로이드 앱 실행속도를 향상시키기 위한 일종의 공용 런타임 같은 것입니다. 그리고 앱이 실행되면 Zygote 에 설정된 내용이 사전에 로드되는데, 아까 언급한 초기화 과정 중에 아래와 같은 내용이 있습니다.

```java
package com.android.internal.os;

/**
 * Startup class for the zygote process.
 *
 * Pre-initializes some classes, and then waits for commands on a UNIX domain
 * socket. Based on these commands, forks off child processes that inherit
 * the initial state of the VM.
 *
 * Please see {@link ZygoteConnection.Arguments} for documentation on the
 * client protocol.
 *
 * @hide
 */
public class ZygoteInit {
    private static final String TAG = "Zygote";

    /**
     * Register AndroidKeyStoreProvider and warm up the providers that are already registered.
     *
     * By doing it here we avoid that each app does it when requesting a service from the
     * provider for the first time.
     */
    private static void warmUpJcaProviders() {
        // ...
        // AndroidKeyStoreProvider.install() manipulates the list of JCA providers to insert
        // preferred providers. Note this is not done via security.properties as the JCA providers
        // are not on the classpath in the case of, for example, raw dalvikvm runtimes.
        AndroidKeyStoreProvider.install();
        Log.i(TAG, "Installed AndroidKeyStoreProvider in "
                + (SystemClock.uptimeMillis() - startTime) + "ms.");
        // ...
    }

    // ...
}
```
**\[리스트 8\]** ZygoteInit.java 의 JCA provider 설치 및 속도향상 과정

```java
package android.security.keystore;

/**
 * A provider focused on providing JCA interfaces for the Android KeyStore.
 *
 * @hide
 */
public class AndroidKeyStoreProvider extends Provider {
    public static final String PROVIDER_NAME = "AndroidKeyStore";

    public AndroidKeyStoreProvider() {
        super(PROVIDER_NAME, 1.0, "Android KeyStore security provider");
        // ...
    }

    /**
     * Installs a new instance of this provider.
     */
    public static void install() {
        // ....

        Security.addProvider(new AndroidKeyStoreProvider());
        // ...
    }
}
```
**\[리스트 9\]** AndroidKeyStoreProvider.java - "AndroidKeyStore" 라는 이름의 JCA provider 등록 과정

이런 일련의 과정을 거쳐 시스템에서 등록한 `AndroidKeyStore` 라는 이름으로 Android KeyStore 서비스에 접근할 수 있게 됩니다. 그리고 안드로이드에서 사용 가능한 KeyStore provider 들의 종류를 뽑아보면, 아래와 같은 결과가 나타납니다.

```java
// List all security providers
for (Provider p : java.security.Security.getProviders()) {
    System.out.println(String.format("== %s ==", p.getName()));
    for (Provider.Service s : p.getServices()) {
        System.out.println(String.format("- %s", s.getAlgorithm()));
    }
}

output:
== AndroidKeyStoreBCWorkaround ==
== AndroidOpenSSL ==
...
== AndroidKeyStore ==
    - AndroidKeyStore
    - HmacSHA256
    - AES
    ...
```

**\[리스트 10\]** 안드로이드 M(6.0.1)에서 지원하는 KeyStore provider 목록

### (중요) AndroidKeyStore 의 Hardware 레벨 지원 여부 확인
다시 [Android KeyStore](https://developer.android.com/training/articles/keystore) 시스템의 설명으로 돌아가 봅시다. 

> Key material of Android Keystore keys is protected from extraction using two security measures:
>
> ... 
>
> Key material may be bound to the secure hardware (e.g., Trusted Execution Environment (TEE), Secure Element (SE)) of the Android device. When this feature is enabled for a key, its key material is never exposed outside of secure hardware.

> Android KeyStore 는 키의 추출을 방지하기 위해 두 가지 보안 조치를 사용합니다:
>
> ...
>
> 키는 안드로이드 기기의 보안 하드웨어(e.g., Trusted Execution Environment (TEE), Secure Element (SE)) 에서만 동작할 수 있습니다. 이 기능이 활성화되면 키는 절대로 보안 하드웨어 밖으로 노출되지 않습니다. 

그런가보다 싶지만 유심히 읽어봐야 할 대목이 있습니다. 바로 *Key material **may be** bound to ...* 부분입니다. **is** 가 아니라 **may be** 랍니다. 즉, 키가 하드웨어에 저장되지 않을 수도 있다는 사실입니다. 물론 문서에는 언급되어 있지 않지만 안드로이드 시스템 특징상 제조원가 절감을 위해 디바이스 제조사들이 KeyStore 를 소프트웨어로 구현할 수도 있다는 뜻입니다. AOSP 의 [Keymaster 구현](https://android.googlesource.com/platform/system/keymaster/+/master/auth_encrypted_key_blob.cpp#31)을 살펴보면 `sw_enforced` 라는 키워드가 있습니다. 이 keymaster API 를 하드웨어 제조사에서 [Keymaster HAL](https://source.android.com/security/keystore) 을 통해 호출하는데 만약 `sw_enforced` 인스턴스를 넘기는 형태로 구현할 경우 그 하드웨어는 KeyStore 를 지원하지만 (API Level 18), 그것이 반드시 별도의 보안 하드웨어 위에서 동작한다고 말할 수는 없습니다.

그리고 "Inside Android Security" 의 저자 Nicolay Elenkov 에 의하면 [Android M 이전의 Software-backed KeyStore 는 root 된 기기에서 유출 가능](https://nelenkov.blogspot.com/2015/06/keystore-redesign-in-android-m.html)하다고 합니다. 링크의 내용이 다소 길기 때문에 요약하자면 software 기반의 KeyStore 구현은 키를 `/data/misc/keystore/user_X`(여기서 X 는 uid - 시스템이 앱마다 부여하는 id)에 저장하는데 이 파일의 내용은 [keystore-decryptor](https://github.com/nelenkov/keystore-decryptor) 로 풀어볼 수 있다고 합니다. 그리고 하드웨어 보안을 지원하지 않는 기기를 확보하지 못해 실 기기에서는 확인할 수 없었습니다만, 에뮬레이터에서 실제로 확인해 본 결과 사실이었습니다.

**즉, (Android KeyStore)를 쓰더라도 Android M 이전의 기기에서는 우리 앱의 데이터가 100% 안전하다는 장담을 할 수는 없습니다. 아직까지 이 문제를 해결할 방법은 찾지 못했습니다만 아래와 같은 로직으로 '이 기기에서의 앱 실행은 안전하지 않을 수 있다' 같은 안내를 띄우는 정도의 가이드는 개발 가능합니다.**

```kotlin
val privKey = (keyEntry as KeyStore.PrivateKeyEntry).privateKey
val factory = KeyFactory.getInstance(privKey.getAlgorithm(), "AndroidKeyStore")
val keyInfo: KeyInfo
try {
    keyInfo = factory.getKeySpec(privKey, KeyInfo::class.java)
    println("HARDWARE-BACKED KEY???? " + keyInfo.isInsideSecureHardware)
} catch (e: InvalidKeySpecException) {
    // Not an Android KeyStore key.
    e.printStackTrace()
}
```

**\[리스트 11\]** KeyInfo API 로 키가 하드웨어로 안전하게 보호되고 있는지를 확인하는 방법

**다행히도 저희가 보유 중인 개발 시료에서 모두 확인해본 결과 모두 `true` 로 확인되는 것으로 보아 전 세계의 대중적인 API Level 18 이상인 Android 기기에서는 KeyStore 를 안심하고 사용할 수 있다는 결론을 얻었습니다.**

다만 API Level L 이전의 Android KeyStore 에는 [사용자가 Lock screen 을 설정하지 않을 경우 초기화](https://doridori.github.io/android-security-the-forgetful-keystore/) 된다거나, 직접 확인하진 못했지만 [앱을 삭제하더라도 KeyStore 가 완전히 초기화되지 않는](https://xzhang35.expressions.syr.edu/wp-content/uploads/2015/10/android_data_residue.pdf) 등의 문제도 있다고 하니 유의하는 것이 좋겠습니다.

## 맺으며
이상으로 KeyStore 를 사용해 데이터를 암호화하는 방법에 대해 알아봤습니다. 저희 하이퍼커넥트에서도 현재 제작 중인 안드로이드 앱 일부에서 이 기능을 탑재해 고객 여러분들의 데이터를 안전하게 보호하려 노력하고 있습니다. 또한 iOS 도 [Secure enclave](https://developer.apple.com/documentation/security/certificate_key_and_trust_services/keys/storing_keys_in_the_secure_enclave)라 하여 비슷한 기능을 제공하고 있으며 역시 저희 개발진은 이 기술의 적극 도입을 위한 노력을 진행 중입니다.

물론 여기 적혀있는 내용들은 Android M(API Level 23) 이후에서만 100% 안전하기 때문에 저희는 그 이전의 안드로이드 버전에서도 [데이터를 안전하게 저장할 방법](http://www.cs.kun.nl/~erikpoll/publications/AndroidSecureStorage.pdf)에 대해 지금도 계속 고민 중입니다.

또한 눈치 빠른 독자분들은 이 기법을 잘 응용하면 외부 저장소에 저장하는 파일도 암호화 할 수 있다는 사실을 깨달으셨을 겁니다. 이 기법은 요즘 데이터 불법 유출로 몸살을 앓고 있는 웹툰 앱들에도 유용합니다. 임시로 다운로드 한 이미지 파일을 KeyStore 가 생성해주는 키로 암호화해 버리고, [WindowManager.LayoutParams#FLAG_SECURE](https://developer.android.com/reference/android/view/WindowManager.LayoutParams#FLAG_SECURE) 를 사용해 화면 캡쳐까지도 막아버린다면 대부분의 어설픈 유출 시도는 손쉽게 막으실 수 있으리라 생각합니다.

꽤 길었던 1부가 끝났습니다. [2부]({% post_url 2018-06-13-android-secure-db-howto %})에서는, 2017년 5월에 소개된 [Room](https://developer.android.com/topic/libraries/architecture/room)을 사용한 안드로이드 데이터베이스를 암호화하는 법에 대해 소개하겠습니다.

## 더 보기
  - [Android KeyStore 시스템](https://developer.android.com/training/articles/keystore)
  - [블록 암호 운용 방식](https://ko.wikipedia.org/wiki/블록_암호_운용_방식)
  - [초기화 벡터](https://ko.wikipedia.org/wiki/초기화_벡터)
  - [문자 인코딩](https://ko.wikipedia.org/wiki/문자_인코딩)
  - [AES 암호화](https://ko.wikipedia.org/wiki/고급_암호화_표준)
  - [RSA 암호화](https://ko.wikipedia.org/wiki/RSA_암호)
  - [Padding(Cryptography)](https://en.wikipedia.org/wiki/Padding_%28cryptography%29)
  - [AOSP KeyStore implementation requirements](https://source.android.com/security/keystore/)
  - [How the Android keystore system can be secure](https://stackoverflow.com/questions/35782807/how-the-android-keystore-system-can-be-secure)
  - [JCA reference guide](https://docs.oracle.com/javase/10/security/java-cryptography-architecture-jca-reference-guide.htm)
  - [Understanding Android zygote and DalvikVM](https://stackoverflow.com/questions/9153166/understanding-android-zygote-and-dalvikvm)
  - [Android Internals](http://www.vogella.com/tutorials/AndroidInternals/article.html#internals)
  - [Keystore redesign in Android M - by Nicolay Elenkov](https://nelenkov.blogspot.com/2015/06/keystore-redesign-in-android-m.html)
  - [Analysis of Secure Key Storage Solutions on Android](http://www.cs.kun.nl/~erikpoll/publications/AndroidSecureStorage.pdf)
