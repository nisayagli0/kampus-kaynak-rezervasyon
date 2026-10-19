# Arayüz tasarım notları

Bu not, raporun "Tasarım Kararları" bölümünün kaynağıdır. Her karar için ne yapıldığı ve neden yapıldığı yazılıdır. Doküman Bölüm 7'deki beş ölçüt başlık olarak kullanıldı: işlem kolaylığı, kompaktlık, uğraştırmama, geri bildirim, görsel kalite.

Bu notlar kodu yazdıktan sonra çıkarıldı. "Doğrulanacaklar" bölümündeki maddeler, uygulama elle denenerek teyit edilecek.

## 0. Temel ilke: arayüzde iş kuralı yoktur

Arayüz hiçbir talebi kendisi engellemez. Geçersiz bir talep de gönderilebilir; reddi ve kodunu rezervasyon modülü verir. Arayüz yalnızca bu kodu Türkçe açıklamaya çevirir (`arayuz/mesajlar.py`).

- **Neden:** Doküman Bölüm 7 bunu zorunlu tutuyor. Ayrıca kural iki yerde yazılırsa biri değiştiğinde ikisi birbirinden ayrılır.
- **Nasıl:** Tüm komutlar tek kapıdan geçer (`arayuz/oturum.py`). Oturum komutu modüle iletir, sonucu olay günlüğüne yazar ve ekranlara haber verir. Ekranlar veriyi yalnızca `okuma.py` ve modülün sonuçlarından okur.
- **Küçük istisna:** Giriş, Çıkış ve İptal düğmeleri rezervasyonun durumuna göre soluk görünür (örneğin tamamlanmış rezervasyonda üçü de pasif). Bu yalnızca gösterim kolaylığıdır; durum geçişlerinin doğruluğunu yine modül denetler. Giriş penceresi gibi zamana bağlı kurallar düğmeye yansıtılmadı, düğme açık kalır ve red modülden gelir.

## 1. Görsel kalite

**Durum rengi, desen ve yazı birlikte.** Her rezervasyon durumu üç şekilde ayırt edilir: renk, desen ve kutunun içindeki yazı etiketi (`arayuz/stil.py`).

| Durum | Renk | Desen | Etiket |
|---|---|---|---|
| Onaylı | mavi | dolu | Onaylı |
| Kullanımda | yeşil | dolu | Kullanımda |
| Tamamlandı | gri-mavi | dolu | Tamamlandı |
| İptal | kırmızı | eğik çizgi | İptal |
| Gelmedi | turuncu | ters eğik çizgi | Gelmedi |
| Bakım | koyu gri | çapraz ızgara | Bakım |
| Hazırlık süresi | soluk sarı | dolu | (etiketsiz) |

- **Neden:** Yalnızca renkle ayırt etmek, renk körlüğü olan kullanıcılarda ve siyah-beyaz çıktıda bilgiyi kaybettirir. Desen ve yazı, renk görünmese de durumu okutur.
- **Neden iptal ve gelmeyen deseli, geçerli olanlar dolu?** Takvimin asıl işi doluluğu göstermek. Doluluğa sayılan durumlar (onaylı, kullanımda) dolu ve yoğun görünür; sayılmayanlar (iptal, gelmedi) çizgili ve açık görünür. Yoğun bir günde bile "hangileri gerçekten yer tutuyor" bir bakışta anlaşılır.
- **Hazırlık süresi** rezervasyonun hemen yanında, çok soluk bir renkle çizilir. Dikkati rezervasyona bırakır, ama kaynağın o sırada neden boş olmadığını açıklar.
- **Simüle saat çizgisi** kırmızı ve kalındır. Kırmızı, "şimdi" için ayrılmış tek renktir; üst çubuktaki saat etiketi de aynı kırmızıdır. Böylece takvimdeki çizgi ile üst çubuktaki saat birbirine bağlanır.
- Renk ve yazı tipi yalnızca `stil.py` içinde tanımlıdır. Başka hiçbir dosyada renk kodu yazılmadı; tutarlılığı tek yer sağlıyor.
- **Açıklama şeridi** takvimin altında durur; kullanıcı hangi rengin neyi gösterdiğini aramak zorunda kalmaz.

## 2. Kompaktlık

**Tek ana pencere, ayrı pencere yok.** Takvim solda, işlem sekmeleri sağda, olay günlüğü altta. Bir işlem için gereken her şey aynı anda ekranda.

- **Rezervasyon ayrıntı kartı takvimin hemen altında.** Kutuya tıklayınca bilgi ve eylem düğmeleri aynı yerde görünür; ekran değişmez.
- **Olay günlüğü katlanabilir.** Başlığındaki işaret kaldırılınca gizlenir ve takvime yer açar.
- **Alt satırlar.** Aynı kaynakta çakışan kutular (örneğin bir rezervasyon ve iptal edilmiş eski bir rezervasyon) üst üste binmez, alt satıra iner. Geçerli rezervasyonlar her zaman ilk satırda kalır; böylece gerçek doluluk hep aynı çizgide okunur.
- **Kaydırma:** Takvim satır yüksekliği küçük tutuldu (tek satırlı kaynak yaklaşık 37 piksel). Kaynak sayısı pencereye sığmayacak kadar artarsa yalnızca takvim alanı kayar; üst çubuk, kart, sağ paneller ve günlük sabit kalır.
- **Dar kutularda etiket kısalır.** Kutu "kullanıcı · durum" yazısını sığdıramıyorsa yalnızca kullanıcıyı yazar. Okunmayan kesik yazı yerine kısa ama tam yazı tercih edildi.

## 3. Uğraştırmama

**Yazı yazmak yerine seçim.** Kaynak, kullanıcı, gün ve saat listelerden ve takvim seçicisinden seçilir. Yazı yazılan tek yerler yeni kullanıcı ve kaynak ekleme penceresindeki kimlik ve ad alanlarıdır (bunlar doğası gereği yeni bilgi).

**Anlamlı varsayılanlar:**
- Gün, takvimde seçili gündür. Takvim ile form aynı güne bağlıdır; birinde gün değişince diğeri de değişir.
- Başlangıç saati, simüle saatten sonraki ilk 15 dakikalık andır (gün başka bir günse 08:00). Bitiş, başlangıçtan 1 saat sonradır. Geçmişte kalan bir saat önerilmez.
- Yeni kullanıcı penceresinde bakiye, seçilen rolün haftalık kotasına otomatik eşitlenir. Kimlik için kullanılmayan bir sonraki numara önerilir.
- Yeni kaynak penceresinde kimlik ve ad, aynı türdeki kaynakların adlandırmasına uyarak önerilir (örneğin YAZ-2 varsa YAZ-3). İzinli roller varsayılan olarak hepsi işaretlidir.
- Saat ilerletmede sık kullanılan sıçramalar tek düğmedir: +15 dk, +1 saat, ertesi gün 08:00, sonraki Pazartesi 08:00.

**Onay penceresi yok.** İptal gibi geri alınamaz işlemlerde bile ek bir "emin misiniz" penceresi çıkmaz. İptalin sonucu (iade, bakiye, güvenilirlik) aynı kartta görünür; yanlış iptalin sonucu görünür olduğu için maliyeti anlaşılır.

**Bekleme kaydı için bilgi yeniden girilmez.** Talep KESISME veya HAZIRLIK_IHLALI ile reddedilince, red mesajının altında "Bekleme kaydı aç" düğmesi belirir. Düğme son talebin bilgilerini aynen kullanır.

**Takvimden form doldurma.** Takvimde boş bir yere tıklamak, talep formunu o kaynak ve saatle (15 dakikaya yuvarlanmış) doldurur.

## 4. Geri bildirim

**Her sonuç, işlemin yapıldığı yerin yakınında görünür.**
- Talep formunun sonucu formun altında.
- Paket talebinde her kalemin sonucu (geçti / reddedildi ve nedeni) o kalemin kendi satırında; paketin genel sonucu altta.
- Giriş, Çıkış, İptal sonucu işlemin yapıldığı şeritte (takvim kartında veya kullanıcı panelinde). İptalde iade, bakiye, güvenilirlik ve bekleme listesinden yapılan otomatik atamalar da aynı yerde yazar.
- Saat ilerletme sonucu, oluşan olaylar listesiyle birlikte saat sekmesinde.
- Ekleme penceresinde red olursa pencere kapanmaz; kod ve Türkçe açıklama aynı pencerede görünür ve değer düzeltilip yeniden denenebilir.

**Başarı yeşil, red kırmızı.** Mesaj renkleri tek yerde (`stil.py`) tanımlı.

**Otomatik güncelleme.** Durumu değiştiren her komuttan sonra takvim, kullanıcı paneli, simüle saat ve olay günlüğü kendiliğinden yenilenir. Kullanıcı ayrıca bir şey yapmaz.

**Olay günlüğü.** Oturumdaki her işlem sırayla listelenir. Satıra tıklayınca komutun JSON karşılığı ve modülün döndürdüğü sonuç (Bölüm 5 biçimi) yan yana görünür. Böylece ekranda görülenle modülün gerçek çıktısı karşılaştırılabilir.

## 5. İşlem kolaylığı (tıklama sayıları)

Aşağıdaki sayılar tasarımdan çıkarıldı; uygulama üzerinde elle sayılıp teyit edilecek (aşağıya bakın).

| Sık işlem | Adım |
|---|---|
| Yeni rezervasyon (kullanıcı seçili) | boş yere tıkla, Rezervasyon yap: 2 |
| Giriş, Çıkış veya İptal | rezervasyon kutusuna tıkla, düğme: 2 |
| Fiyat sorma | Fiyatı göster: 1 (form dolu) |
| Reddedilen talep için bekleme kaydı | Bekleme kaydı aç: 1 |
| Saat ilerletme (sık sıçramalar) | düğme: 1 |
| Kullanıcı değiştirme | talep formunun üstündeki listeden seç: 2 |

Kullanıcı seçici hem talep formunun üstünde hem Kullanıcı sekmesinde olduğundan, kullanıcı değiştirmek için sekme değiştirmek gerekmez.

## 6. Parametre bağımsızlığı

Rol, tür, sertifika, kaynak listeleri ve saat başlangıç dosyasından gelir. Kodda sabit rol veya tür adı yoktur. Dosya değiştirilince (`Başlangıç dosyası seç`) durum baştan kurulur; takvim, panel, saat ve günlük sıfırlanır. Seçilen dosya hatalıysa eski durum korunur ve hata üst çubukta görünür.

## Doğrulanacaklar

- [ ] Tıklama sayıları (bölüm 5) uygulama üzerinde elle sayıldı mı?
- [ ] Yoğun günde (15-20 rezervasyon) takvim okunuyor mu? (Ekran görüntüsü alınacak.)
- [ ] Yüksek çözünürlüklü ekranda ve farklı pencere boyutunda yerleşim bozulmuyor mu?
- [ ] Renkler siyah-beyaz çıktıda ayırt edilebiliyor mu? (Desen ve yazı etiketi var; çıktıdan bakılacak.)
- [ ] Aşağıdaki iki tasarım kararı tartışmaya açık: onay penceresinin tamamen olmaması, ve Giriş penceresinin düğmeye yansıtılmaması. Demoda sorulursa gerekçe bölüm 3 ve bölüm 0'da.
