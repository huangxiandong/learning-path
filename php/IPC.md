# PHP IPC

## Advisory File Lock
�ļ�����flock����ʵ�֡��������ڷ�ֹһ������ִ�����Σ����½�һ��pid�ļ�����pid���롣pid�����÷���signal�� ��demo��

## socket and stream
��ã����Ҳ������ڵ���

## signal
�źŲ��ܴ������ݣ�ֻ�ܸ����ź����ûص���
��Ҫ declare(tick=1); ��demo��

## msg_queue and semaphore
ģ������Ϊ sysvmsg, sysvsem, sysvshm
msg_get_queue �����ܴ������ݡ���demo��

## pipe
��һЩ���ƣ��� pcntl_fork ���ӽ���û�취�õ� $fd, ò������Ϊ�ӽ��̵�$fd�ǴӸ����̸��ƶ����� 
ò����Ҫ�� proc_open �򿪵Ľ��̲��ܵõ� $fd

## shared memory
ģ������Ϊ shmop�� ����Ĭ��û���ṩͬ���Ļ��ƣ�ֻ�� shmop_open �Ĳ��� $flagΪ "n"ʱ�����ȼ��ͬkey���ڴ��Ƿ���ڣ������򲻴����� set, get ��ͬ��������ò�ƿ��Խ��� sem_get, sem_remove, sem_acquire, sem_release ��ʵ�֡��ź���������ԭ�Ӳ�����
sem_get �����ź���
sem_remove ɾ���ź�����һ�㲻�ã�
sem_acquire ����õ��ź���
sem_release �ͷ��ź������� sem_acquire �ɶ�ʹ�á�

int ftok ( string $pathname , string $proj ) �ļ���һ��ʹ����Ŀ�е��ļ���������existing, accessable���ļ���$proj ��Ŀid����Ϊ���ַ��ַ����� �ļ���ʹ�� /tmp ��һ��ϵͳ·��Ҳ�ǿ��ԣ�ֻ�������ܻ�����������ظ���ֻʣ��id��Ϊ���֣��������������Ų顣

## sync ģ��
��װ�� pecl install sync
������ SyncMutex, SyncSemaphore, SyncReaderWriter, SyncEvent �ĸ��ࡣ ��д�������������ź���ò����sysvsemģ��ķ�װ��Event ��֪��ʲô���á�
�ĵ���д SyncSemaphore �� SyncMutex �������ǣ� SyncSemaphore����һ�α�������̣��̣߳����ʣ� ��Mutexһ��ֻ�ܱ�һ�����̵õ���
SyncEvent���ڶ������ʹ�á�һ������wait��������һ�����̿���fire�¼���ʹ�õ�һ�����̼������С�

## pthreads
Ҳ������һ�� Metex �ࡣ���� Cond, Pool�� ò��ֻ�о�̬������ֻ��� thread?








