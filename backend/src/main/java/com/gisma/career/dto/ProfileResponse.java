package com.gisma.career.dto;

import com.gisma.career.model.Skill;
import com.gisma.career.model.Student;
import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;
import java.util.stream.Collectors;

@Data
@AllArgsConstructor
public class ProfileResponse {
    private Long id;
    private String email;
    private String name;
    private String university;
    private String course;
    private Integer year;
    private List<String> skills;

    public static ProfileResponse fromEntity(Student s) {
        List<String> skillNames = s.getSkills().stream()
                .map(Skill::getName)
                .sorted()
                .collect(Collectors.toList());
        return new ProfileResponse(
                s.getId(), s.getEmail(), s.getName(),
                s.getUniversity(), s.getCourse(), s.getYear(),
                skillNames);
    }
}
