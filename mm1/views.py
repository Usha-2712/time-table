import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, response
from django.template.loader import get_template
from .models import *
import random as rnd
from. forms import *
from django.views.generic import View

POPULATION_SIZE = 15
NUMB_OF_ELITE_SCHEDULES = 1
TOURNAMENT_SELECTION_SIZE = 3
MUTATION_RATE = 0.05


class Data:
    def __init__(self):
        self._rooms = Room.objects.all()
        self._meetingTimes = MeetingTime.objects.all()
        self._instructors = Instructor.objects.all()
        self._courses = Course.objects.all()
        self._depts = Department.objects.all()

    def get_rooms(self): return self._rooms

    def get_instructors(self): return self._instructors

    def get_courses(self): return self._courses

    def get_depts(self): return self._depts

    def get_meetingTimes(self): return self._meetingTimes

def generate_dic_available_slots():
    dic_available_slots = {}
    for i in MeetingTime.objects.all():
        dic_available_slots[str(i).split()[0]] = []
    return dic_available_slots

def generate_dic_slots():
    dic_available_slots = {}
    for i in MeetingTime.objects.all():
        dic_available_slots[i] = 0
    return dic_available_slots

class Schedule:
    def __init__(self):
        self._data = data
        self._classes = []
        self._numberOfConflicts = 0
        self._fitness = -1
        self._classNumb = 0
        self._isFitnessChanged = True

    def get_classes(self):
        self._isFitnessChanged = True
        return self._classes

    def get_numbOfConflicts(self): return self._numberOfConflicts

    def get_fitness(self):
        if self._isFitnessChanged:
            self._fitness = self.calculate_fitness()
            self._isFitnessChanged = False
        return self._fitness

    def initialize(self):
        sections = Section.objects.all()
        time_slots_dic = generate_dic_available_slots()
        for section in sections:
            dept = section.department
            n = section.num_class_in_week
            if n <= len(MeetingTime.objects.all()):
                courses = dept.courses.all()
                repeat = []
                for course in courses:
                    for i in range(n // len(courses)):
                        crs_inst = course.instructors.all()
                        newClass = Class(self._classNumb, dept, section.section_id, course)
                        self._classNumb += 1
                        m = data.get_meetingTimes()[rnd.randrange(0, len(MeetingTime.objects.all()))] 
                        while m in repeat:
                            m = data.get_meetingTimes()[rnd.randrange(0, len(MeetingTime.objects.all()))]
                        repeat.append(m)
                        newClass.set_meetingTime(m)
                        #print(str(m).split()[0])
                        r = data.get_rooms()[rnd.randrange(0, len(data.get_rooms()))]
                        while r in time_slots_dic[str(m).split()[0]]:
                            r = data.get_rooms()[rnd.randrange(0, len(data.get_rooms()))]
                        newClass.set_room(r)
                        time_slots_dic[str(m).split()[0]].append(r)
                        newClass.set_instructor(crs_inst[rnd.randrange(0, len(crs_inst))])
                        self._classes.append(newClass)
            else:
                n = len(MeetingTime.objects.all())
                courses = dept.courses.all()
                for course in courses:
                    for i in range(n // len(courses)):
                        crs_inst = course.instructors.all()
                        newClass = Class(self._classNumb, dept, section.section_id, course)
                        self._classNumb += 1
                        newClass.set_meetingTime(data.get_meetingTimes()[rnd.randrange(0, len(MeetingTime.objects.all()))])
                        newClass.set_room(data.get_rooms()[rnd.randrange(0, len(data.get_rooms()))])
                        newClass.set_instructor(crs_inst[rnd.randrange(0, len(crs_inst))])
                        self._classes.append(newClass)

        return self

    def calculate_fitness(self):
        self._numberOfConflicts = 0
        classes = self.get_classes()
        #print(classes)
        for i in range(len(classes)):
            if classes[i].room.seating_capacity < int(classes[i].course.max_numb_students):
                self._numberOfConflicts += 1
            for j in range(len(classes)):
                if j >= i:
                    if (classes[i].meeting_time == classes[j].meeting_time) and \
                            (classes[i].section_id != classes[j].section_id) and (classes[i].section == classes[j].section):
                        if classes[i].room == classes[j].room:
                            self._numberOfConflicts += 1
                        if classes[i].instructor == classes[j].instructor:
                            self._numberOfConflicts += 1
        newtimes = []
        for i in range(len(classes)):
                #print(classes[i].meeting_time)
                if(classes[i].meeting_time in newtimes):
                    self._numberOfConflicts += 1
                else :
                    newtimes.append(classes[i].meeting_time)
        return 1 / (1.0 * self._numberOfConflicts + 1)
    

class Population:
    def __init__(self, size):
        self._size = size
        self._data = data
        self._schedules = [Schedule().initialize() for i in range(size)]

    def get_schedules(self):
        return self._schedules


class GeneticAlgorithm:
    def evolve(self, population):
        return self._mutate_population(self._crossover_population(population))

    def _crossover_population(self, pop):
        crossover_pop = Population(0)
        for i in range(NUMB_OF_ELITE_SCHEDULES):
            crossover_pop.get_schedules().append(pop.get_schedules()[i])
        i = NUMB_OF_ELITE_SCHEDULES
        while i < POPULATION_SIZE:
            schedule1 = self._select_tournament_population(pop).get_schedules()[0]
            schedule2 = self._select_tournament_population(pop).get_schedules()[0]
            crossover_pop.get_schedules().append(self._crossover_schedule(schedule1, schedule2))
            i += 1
        return crossover_pop

    def _mutate_population(self, population):
        for i in range(NUMB_OF_ELITE_SCHEDULES, POPULATION_SIZE):
            self._mutate_schedule(population.get_schedules()[i])
        return population

    def _crossover_schedule(self, schedule1, schedule2):
        crossoverSchedule = Schedule().initialize()
        for i in range(0, len(crossoverSchedule.get_classes())):
            if rnd.random() > 0.5:
                crossoverSchedule.get_classes()[i] = schedule1.get_classes()[i]
            else:
                crossoverSchedule.get_classes()[i] = schedule2.get_classes()[i]
        return crossoverSchedule

    def _mutate_schedule(self, mutateSchedule):
        schedule = Schedule().initialize()
        for i in range(len(mutateSchedule.get_classes())):
            if MUTATION_RATE > rnd.random():
                mutateSchedule.get_classes()[i] = schedule.get_classes()[i]
        return mutateSchedule

    def _select_tournament_population(self, pop):
        tournament_pop = Population(0)
        i = 0
        while i < TOURNAMENT_SELECTION_SIZE:
            tournament_pop.get_schedules().append(pop.get_schedules()[rnd.randrange(0, POPULATION_SIZE)])
            i += 1
        tournament_pop.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
        return tournament_pop


class Class:
    def __init__(self, id, dept, section, course):
        self.section_id = id
        self.department = dept
        self.course = course
        self.instructor = None
        self.meeting_time = None
        self.room = None
        self.section = section

    def get_id(self): return self.section_id

    def get_dept(self): return self.department

    def get_course(self): return self.course

    def get_instructor(self): return self.instructor

    def get_meetingTime(self): return self.meeting_time

    def get_room(self): return self.room

    def set_instructor(self, instructor): self.instructor = instructor

    def set_meetingTime(self, meetingTime): self.meeting_time = meetingTime

    def set_room(self, room): self.room = room


data = Data()


def context_manager(schedule):
    classes = schedule.get_classes()
    context = []
    cls = {}
    for i in range(len(classes)):
        cls["section"] = classes[i].section_id
        cls['dept'] = classes[i].department.dept_name
        cls['course'] = f'{classes[i].course.course_name} ({classes[i].course.course_number}, ' \
                        f'{classes[i].course.max_numb_students}'
        cls['room'] = f'{classes[i].room.r_number} ({classes[i].room.seating_capacity})'
        cls['instructor'] = f'{classes[i].instructor.name} ({classes[i].instructor.uid})'
        cls['meeting_time'] = [classes[i].meeting_time.pid, classes[i].meeting_time.day, classes[i].meeting_time.time]
        context.append(cls)
    return context


def home(request):
    return render(request, 'index.html', {})

def time_slots():
#    return ['9:30-10:30','10:30-11:30','11:30-12:30','12:30-1:30','2:30-3:30','3:30-4:30','4:30-5:30','4:30-5:30']
   return ['9:30-10:30','10:30-11:30','11:30-12:30','12:30-1:30','2:30-3:30','3:30-4:30']

def time_slots_start():
#    return ['9:30','10:30','11:30','12:30','2:30','3:30','4:30','4:30']
   return ['9:30','10:30','11:30','12:30','2:30','3:30']

def days():
    return ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']

def sec_list():
    li = []
    for section in Section.objects.all():
        li.append(str(section).split("(")[1][:-1])
    return li

def restructure(tt):
    time_slots = time_slots_start()
    days_slot = days()
    #sec_list = sec_list()
    result = dict()
    for k,sec in tt.items() :
        print(k)
        time_table = dict()
        #print(len(days_slots),len(time))
        for i in range(len(days_slot)):
            time_table[days_slot[i]] = [None for j in range(len(time_slots))]
        #print(timetable)
        for key,value in sec.items():
            #print(key,value)
            if len(value)!=0:
                day = value[5].split()[1]
                time = value[5].split()[2]
                day_index = days_slot.index(day)
                time_index = time_slots.index(time)
                time_table[day][time_index] = ["".join(value[2].split()[1:]),value[3],"".join(value[4].split()[1:])]
        print(time_table)
        result[k] = time_table
    return result

def timetable(request):
    schedule = []
    population = Population(POPULATION_SIZE)
    generation_num = 0
    population.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
    geneticAlgorithm = GeneticAlgorithm()
    while population.get_schedules()[0].get_fitness() != 1.0:
        generation_num += 1
        if(generation_num>2):break
        print('\n> Generation #' + str(generation_num)+" "+str(population.get_schedules()[0].get_fitness()))
        population = geneticAlgorithm.evolve(population)
        population.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
        schedule = population.get_schedules()[0].get_classes()
    print('\n> Generation #' + str(generation_num)+" "+str(population.get_schedules()[0].get_fitness()))
    # slots = []
    # dic_available_slots = {}
    # for i in MeetingTime.objects.all():
    #     slots.append(str(i).split()[0])
    #     dic_available_slots[str(i).split()[0]] = 0
    # for section in Section.objects.all():
    #     print(section) 
    #     alloted_slots = []
    #     colliding_slots = []
    #     dic_available_slots = generate_dic_available_slots()
    #     for sclass in schedule:
    #         if sclass.section == section.section_id :
    #             #print(str(sclass.section_id)+" "+str(sclass.course)+" "+str(sclass.room)+" "+str(sclass.instructor)+" "+str(sclass.meeting_time))
    #             #print(str(sclass.meeting_time).split()[0])
    #             time = str(sclass.meeting_time).split()[0]
    #             if(dic_available_slots[time]==0):
    #                 dic_available_slots[time] = 1
    #             else:
    #                 dic_available_slots[time] += 1
    #                 colliding_slots.append([sclass.section_id,sclass.course,sclass.room,sclass.instructor,sclass.meeting_time,time])
    #     # for key,value in dic_available_slots.items():
    #     #     print(key,value)
    #     not_allocated_slots = []
    #     for key,value in dic_available_slots.items():
    #         if(value==0):
    #             not_allocated_slots.append([key,value])
    #     print(colliding_slots)
    #     for i in colliding_slots:
    #         print(i)
    #         instru_slots = []
    #         for s in Section.objects.all():
    #                 for sc in schedule:
    #                    if sc.section == s.section_id :
    #                        if str(sc.instructor) == str(i[3]):
    #                             instru_slots.append(str(sc.meeting_time))
    #         print(instru_slots)
    #         newtime_slot = []
    #         for k in not_allocated_slots :
    #             if k not in instru_slots :
    #                 print(k)
    #                 newtime_slot.append(k)
    #                 break
    #         rooms_occupied = []
    #         for s in Section.objects.all():
    #                 for sc in schedule:
    #                    if sc.section == s.section_id :
    #                        #print(str(sc.meeting_time).split()[0] ,str(newtime_slot[0][0]))
    #                        if str(sc.meeting_time).split()[0] == str(newtime_slot[0][0]):
    #                             rooms_occupied.append(sc.room)
    #         print(rooms_occupied)
    tt = dict()   
    section_list = []    
    Meeting_list = []
    timings = []
    t = 0
    for i in MeetingTime.objects.all():
        Meeting_list.append(str(i))  
    for section in Section.objects.all() :
        #print(section)
        section_list.append(str(section))
        tt[str(section).split("(")[1][:-1]] = generate_dic_available_slots()
        for sc in schedule:
            if sc.section == section.section_id :
                tt[str(section).split("(")[1][:-1]][str(sc.meeting_time).split()[0]] = [str(section).split("(")[1][:-1],str(sc.section_id),str(sc.course),str(sc.room),str(sc.instructor),str(sc.meeting_time)]
        #print(tt[section][0])
    #print(tt)
    time_table = restructure(tt)
    return render(request, 't1.html', {'schedule': time_table, 'sections': section_list,
                                              'times': Meeting_list,'timings' : time_slots()})
    # return render(request, 'timetable.html', {'schedule': schedule, 'sections': Section.objects.all(),
    #                                           'times': MeetingTime.objects.all()})



def add_instructor(request):
    form = InstructorForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addinstructor')
    context = {
        'form': form
    }
    return render(request, 'adins.html', context)


def inst_list_view(request):
    context = {
        'instructors': Instructor.objects.all()
    }
    return render(request, 'instlist.html', context)


def delete_instructor(request, pk):
    inst = Instructor.objects.filter(pk=pk)
    if request.method == 'POST':
        inst.delete()
        return redirect('editinstructor')


def add_room(request):
    form = RoomForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addroom')
    context = {
        'form': form
    }
    return render(request, 'addrm.html', context)


def room_list(request):
    context = {
        'rooms': Room.objects.all()
    }
    return render(request, 'rmlist.html', context)


def delete_room(request, pk):
    rm = Room.objects.filter(pk=pk)
    if request.method == 'POST':
        rm.delete()
        return redirect('editrooms')


def meeting_list_view(request):
    context = {
        'meeting_times': MeetingTime.objects.all()
    }
    return render(request, 'mtlist.html', context)


def add_meeting_time(request):
    form = MeetingTimeForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addmeetingtime')
        else:
            print('Invalid')
    context = {
        'form': form
    }
    return render(request, 'addmt.html', context)


def delete_meeting_time(request, pk):
    mt = MeetingTime.objects.filter(pk=pk)
    if request.method == 'POST':
        mt.delete()
        return redirect('editmeetingtime')


def course_list_view(request):
    context = {
        'courses': Course.objects.all()
    }
    return render(request, 'crslist.html', context)


def add_course(request):
    form = CourseForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addcourse')
        else:
            print('Invalid')
    context = {
        'form': form
    }
    return render(request, 'adcrs.html', context)


def delete_course(request, pk):
    crs = Course.objects.filter(pk=pk)
    if request.method == 'POST':
        crs.delete()
        return redirect('editcourse')


def add_department(request):
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('adddepartment')
    context = {
        'form': form
    }
    return render(request, 'addep.html', context)


def department_list(request):
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'deptlist.html', context)


def delete_department(request, pk):
    dept = Department.objects.filter(pk=pk)
    if request.method == 'POST':
        dept.delete()
        return redirect('editdepartment')


def add_section(request):
    form = SectionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('addsection')
    context = {
        'form': form
    }
    return render(request, 'addsec.html', context)


def section_list(request):
    context = {
        'sections': Section.objects.all()
    }
    return render(request, 'seclist.html', context)


def delete_section(request, pk):
    sec = Section.objects.filter(pk=pk)
    if request.method == 'POST':
        sec.delete()
        return redirect('editsection')

