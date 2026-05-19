package com.gisma.career.service;

import com.gisma.career.model.Skill;
import com.gisma.career.model.Student;
import com.gisma.career.repository.SkillRepository;
import com.gisma.career.repository.StudentRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class SkillService {

    private final SkillRepository skillRepository;
    private final StudentRepository studentRepository;

    public SkillService(SkillRepository skillRepository, StudentRepository studentRepository) {
        this.skillRepository = skillRepository;
        this.studentRepository = studentRepository;
    }

    public List<Skill> allSkills() {
        return skillRepository.findAll();
    }

    @Transactional
    public Student addSkillToStudent(Student student, String skillName) {
        String trimmed = skillName.trim();
        Skill skill = skillRepository.findByNameIgnoreCase(trimmed)
                .orElseGet(() -> skillRepository.save(Skill.builder().name(trimmed).build()));
        student.getSkills().add(skill);
        return studentRepository.save(student);
    }

    @Transactional
    public Student removeSkillFromStudent(Student student, String skillName) {
        student.getSkills().removeIf(s -> s.getName().equalsIgnoreCase(skillName.trim()));
        return studentRepository.save(student);
    }
}
